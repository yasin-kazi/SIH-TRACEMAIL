"""Standard-library runnable integration tests for the canonical EML path."""
import hashlib
import asyncio
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

from .isolation import set_test_database_env, test_db_path, teardown_database


class EmlVerticalSliceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        set_test_database_env()
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.previous_cwd = os.getcwd()
        os.chdir(cls.temp_dir.name)
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from fastapi.testclient import TestClient
        from main import app
        cls.client = TestClient(app)
        cls.client.__enter__()
        cls.fixture = Path(__file__).parent / "fixtures" / "valid.eml"

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)
        teardown_database()
        os.chdir(cls.previous_cwd)
        cls.temp_dir.cleanup()

    def test_upload_creates_case_and_preserves_original_bytes(self):
        raw = self.fixture.read_bytes()
        response = self.client.post("/api/cases/upload", files={"file": ("valid.eml", raw, "message/rfc822")})
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["source_type"], "eml_upload")
        self.assertEqual(payload["analysis_status"], "completed")
        self.assertTrue(payload["evidence_id"])

        case_id = payload["case_id"]
        self.assertEqual(self.client.get("/api/cases").status_code, 200)
        for path in [f"/api/cases/{case_id}", f"/api/cases/{case_id}/identity", f"/api/cases/{case_id}/evidence", f"/api/cases/{case_id}/headers", f"/api/cases/{case_id}/transit-hops", f"/api/cases/{case_id}/infrastructure", f"/api/cases/{case_id}/graph", f"/api/cases/{case_id}/campaign", f"/api/cases/{case_id}/timeline", f"/api/copilot/{case_id}/messages"]:
            self.assertEqual(self.client.get(path).status_code, 200, path)
        self.assertEqual(self.client.post(f"/api/reports/{case_id}/generate").status_code, 200)
        report_response = self.client.get(f"/api/reports/{case_id}")
        self.assertEqual(report_response.status_code, 200)
        self.assertEqual(self.client.post(f"/api/copilot/{case_id}/ask", json={"question": "What is the strongest evidence?"}).status_code, 200)

        # Transit hops must be derived from the actual EML, never fabricated.
        hops_response = self.client.get(f"/api/cases/{case_id}/transit-hops").json()
        for hop in hops_response["hops"]:
            hop_text = f"{hop['label']} {hop['ip']} {hop['description']}"
            self.assertNotIn("mx.company.com", hop_text)

        # Report must not claim facts that were not established from evidence.
        report = report_response.json()
        report_text = " ".join([
            report.get("executive_summary", ""),
            report.get("evidence_analysis", ""),
            report.get("identity_analysis", ""),
            report.get("infrastructure_analysis", ""),
            report.get("campaign_correlation", ""),
            report.get("attack_path", ""),
            report.get("confidence_and_limitations", ""),
            report.get("conclusion", ""),
        ]).lower()
        for unsupported in ["third-party smtp relay", "has been flagged in", "registered", "privacy proxy registration"]:
            self.assertNotIn(unsupported, report_text)

        # Copilot must not claim registration data without WHOIS/RDAP evidence.
        copilot_response = self.client.post(
            f"/api/copilot/{case_id}/ask",
            json={"question": "Tell me about the sender domain and whois"},
        )
        self.assertEqual(copilot_response.status_code, 200)
        copilot_text = copilot_response.json()["content"].lower()
        for unsupported in ["recently registered", "privacy proxy"]:
            self.assertNotIn(unsupported, copilot_text)

        db = sqlite3.connect(test_db_path())
        evidence = db.execute("SELECT sha256, original_bytes, size, status FROM evidence_records WHERE id = ?", (payload["evidence_id"],)).fetchone()
        self.assertEqual(evidence[0], hashlib.sha256(raw).hexdigest())
        self.assertEqual(evidence[1], raw)
        self.assertEqual(evidence[2], len(raw))
        self.assertEqual(evidence[3], "preserved")
        db.close()

    def test_forensic_records_are_persisted_from_mixed_mime_email(self):
        fixture = Path(__file__).parent / "fixtures" / "forensic_mixed.eml"
        raw = fixture.read_bytes()
        response = self.client.post(
            "/api/cases/upload",
            files={"file": ("forensic_mixed.eml", raw, "message/rfc822")},
        )
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        evidence_id = payload["evidence_id"]

        db = sqlite3.connect(test_db_path())
        mime_parts = db.execute(
            "SELECT part_index, parent_index, depth, content_type, is_attachment FROM mime_parts WHERE evidence_id = ? ORDER BY part_index",
            (evidence_id,),
        ).fetchall()
        self.assertEqual(len(mime_parts), 5)
        self.assertEqual(mime_parts[0][0], 1)
        self.assertEqual(mime_parts[0][1], None)
        self.assertEqual(mime_parts[0][3], "multipart/mixed")
        self.assertFalse(mime_parts[0][4])
        self.assertEqual(
            [p[3] for p in mime_parts[1:]],
            ["text/plain", "text/html", "application/pdf", "text/csv"],
        )

        # Received hops are persisted verbatim in file order (oldest leg first).
        hops = db.execute(
            "SELECT sequence, label, hop_type, source_ip, protocol, from_host, by_host FROM received_hops WHERE evidence_id = ? ORDER BY sequence",
            (evidence_id,),
        ).fetchall()
        self.assertEqual(len(hops), 2)
        self.assertEqual(
            hops[0],
            (1, "SOURCE", "source", "192.0.2.8", "ESMTPS", "mx-outbound.example.com", "edge-relay-1.corp-example.test"),
        )
        self.assertEqual(
            hops[1],
            (2, "INBOX", "destination", "192.0.2.7", "SMTP", "phishing-sender.evil-quest.example.net", "mail-1.corp-example.test"),
        )

        # Attachment hashes cover the transfer-decoded payload bytes.
        atts = db.execute(
            "SELECT filename, mime_type, sha256 FROM attachments WHERE evidence_id = ? ORDER BY filename",
            (evidence_id,),
        ).fetchall()
        self.assertEqual(len(atts), 2)
        self.assertEqual(
            atts[0],
            ("invoice.pdf", "application/pdf", "56cd7a52d4dbc4af2f1e64a46b7fd199a4ec569b6dd86c20cd74b1bad746f5c1"),
        )
        self.assertEqual(
            atts[1],
            ("ledger.csv", "text/csv", "67506524668ef4b99583991cfee26b76363c9940a7969f18712f6fe3e42b79a2"),
        )

        # IOCs are observable-only values (no fabricated threat labels).
        iocs = db.execute(
            "SELECT ioc_type, value FROM iocs WHERE evidence_id = ?", (evidence_id,)
        ).fetchall()
        ioc_set = {(ioc_type, value) for ioc_type, value in iocs}
        for expected in [
            ("url", "http://evil-quest.example.net/pay"),
            ("email", "refund@paid-login.example.net"),
            ("domain", "paid-login.example.net"),
            ("domain", "evil-quest.example.net"),
            ("ip", "192.0.2.7"),
            ("ip", "192.0.2.8"),
            ("message_id", "forensic-fixture-002@evil-quest.example.net"),
        ]:
            self.assertIn(expected, ioc_set)

        # Every persisted child carries exactly one evidence relationship.
        rel = db.execute(
            "SELECT target_type, COUNT(*) FROM evidence_relationships WHERE evidence_id = ? GROUP BY target_type",
            (evidence_id,),
        ).fetchall()
        rel_map = dict(rel)
        self.assertEqual(rel_map["mime_part"], 5)
        self.assertEqual(rel_map["received_hop"], 2)
        self.assertEqual(rel_map["attachment"], 2)
        self.assertEqual(rel_map["ioc"], len(ioc_set))
        db.close()

        # Transit-hops endpoint now serves persisted hop records (extra fields).
        hops_resp = self.client.get(f"/api/cases/{payload['case_id']}/transit-hops").json()
        self.assertEqual(len(hops_resp["hops"]), 2)
        self.assertTrue(
            all("sequence" in h and "raw_header" in h and "source_ip" in h for h in hops_resp["hops"])
        )
        self.assertEqual([h["source_ip"] for h in hops_resp["hops"]], ["192.0.2.8", "192.0.2.7"])
        self.assertEqual(
            [h["hop_type"] for h in hops_resp["hops"]],
            ["source", "destination"],
        )

    def test_forensic_apis_expose_persisted_records(self):
        fixture = Path(__file__).parent / "fixtures" / "forensic_mixed.eml"
        raw = fixture.read_bytes()
        response = self.client.post(
            "/api/cases/upload",
            files={"file": ("forensic_mixed.eml", raw, "message/rfc822")},
        )
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        case_id = payload["case_id"]
        evidence_id = payload["evidence_id"]

        # MIME parts: persisted, ordered, refactored metadata only.
        parts = self.client.get(f"/api/cases/{case_id}/mime-parts").json()
        self.assertEqual(len(parts), 5)
        self.assertEqual(parts[0]["content_type"], "multipart/mixed")
        self.assertIsNone(parts[0]["parent_id"])
        self.assertEqual(
            [p["content_type"] for p in parts[1:]],
            ["text/plain", "text/html", "application/pdf", "text/csv"],
        )
        self.assertEqual([p["is_attachment"] for p in parts], [False, False, False, True, True])

        # Attachments: metadata + hash only, never payload bytes.
        attachments = self.client.get(f"/api/cases/{case_id}/attachments").json()
        self.assertEqual(len(attachments), 2)
        by_name = {a["filename"]: a for a in attachments}
        self.assertEqual(
            by_name["invoice.pdf"]["sha256"],
            "56cd7a52d4dbc4af2f1e64a46b7fd199a4ec569b6dd86c20cd74b1bad746f5c1",
        )
        for a in attachments:
            self.assertNotIn("bytes", a)
            self.assertNotIn("payload", a)
            self.assertNotIn("content", a)

        # IOCs: observables only, no verdict fabricated.
        iocs = self.client.get(f"/api/cases/{case_id}/iocs").json()
        ioc_set = {(i["type"], i["value"]) for i in iocs}
        for expected in [
            ("url", "http://evil-quest.example.net/pay"),
            ("email", "refund@paid-login.example.net"),
            ("domain", "paid-login.example.net"),
            ("domain", "evil-quest.example.net"),
            ("ip", "192.0.2.7"),
            ("ip", "192.0.2.8"),
            ("message_id", "forensic-fixture-002@evil-quest.example.net"),
        ]:
            self.assertIn(expected, ioc_set)
        for i in iocs:
            self.assertNotIn("malicious", i)
            self.assertTrue(any(i["type"] == t for t in ("ip", "domain", "url", "email", "message_id", "hash")))

        # Relationships: one per persisted child, evidence as the source node.
        relationships = self.client.get(f"/api/cases/{case_id}/relationships").json()
        rel_map: dict[str, int] = {}
        for r in relationships:
            self.assertEqual(r["relation_type"], "contains")
            self.assertEqual(r["source_type"], "original_email")
            self.assertEqual(r["source_id"], evidence_id)
            self.assertIn(r["target_type"], ("mime_part", "received_hop", "attachment", "ioc"))
            rel_map[r["target_type"]] = rel_map.get(r["target_type"], 0) + 1
        self.assertEqual(rel_map["mime_part"], 5)
        self.assertEqual(rel_map["received_hop"], 2)
        self.assertEqual(rel_map["attachment"], 2)
        self.assertEqual(rel_map["ioc"], len(iocs))

        # Received chain: persisted hops, no fabrication.
        hops = self.client.get(f"/api/cases/{case_id}/transit-hops").json()["hops"]
        self.assertEqual([h["source_ip"] for h in hops], ["192.0.2.8", "192.0.2.7"])
        hop_blob = " ".join(f"{h['label']} {h['ip']} {h['from_host']} {h['by_host']}" for h in hops)
        self.assertNotIn("mx.company.com", hop_blob)

        # Summary counts match the persisted rows and hash the raw uploaded bytes.
        summary = self.client.get(f"/api/cases/{case_id}/forensic-summary").json()
        self.assertEqual(summary["mime_parts"], 5)
        self.assertEqual(summary["received_hops"], 2)
        self.assertEqual(summary["attachments"], 2)
        self.assertEqual(summary["iocs"], len(iocs))
        self.assertEqual(summary["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(summary["source_type"], "eml_upload")
        self.assertEqual(summary["acquisition_method"], "upload")
        self.assertEqual(summary["content_type"], "message/rfc822")
        self.assertEqual(summary["original_filename"], "forensic_mixed.eml")

        # Unknown case → 404 on the new read APIs.
        self.assertEqual(self.client.get("/api/cases/case-999999/mime-parts").status_code, 404)
        self.assertEqual(self.client.get("/api/cases/case-999999/relationships").status_code, 404)

    def test_transit_hops_are_derived_from_received_headers(self):
        from services.email_parser import extract_received_hops_from_text
        eml = (
            "Received: from relay1.smtp.example (relay1.smtp.example [203.0.113.11])\n"
            "\tby mx.corp.example with ESMTPS id xyz789\n"
            "Received: from mail1.origin.example (mail1.origin.example [203.0.113.10])\n"
            "\tby relay1.smtp.example (Postfix) with ESMTPS id abc123\n"
            "From: sender@origin.example\nTo: victim@corp.example\nSubject: t\n\nbody"
        )
        hops = extract_received_hops_from_text(eml)
        self.assertEqual(len(hops), 2)
        self.assertEqual(hops[0]["hop_type"], "source")
        self.assertEqual(hops[-1]["hop_type"], "destination")
        self.assertEqual(hops[0]["ip"], "203.0.113.10")
        self.assertTrue(hops[0]["description"].startswith("mail1.origin.example"))
        self.assertIsInstance(hops[1], dict)
        self.assertFalse(any("mx.company.com" in (h["ip"] + h["description"]) for h in hops))
        self.assertEqual(extract_received_hops_from_text(
            "From: a@example.test\nTo: b@example.test\nSubject: t\n\nno received headers"
        ), [])

    def test_invalid_upload_returns_useful_error(self):
        response = self.client.post("/api/cases/upload", files={"file": ("not-email.txt", b"no", "text/plain")})
        self.assertEqual(response.status_code, 400)
        self.assertIn(".eml", response.json()["detail"])

    def test_report_and_copilot_are_evidence_grounded(self):
        fixture = Path(__file__).parent / "fixtures" / "forensic_mixed.eml"
        raw = fixture.read_bytes()
        response = self.client.post(
            "/api/cases/upload",
            files={"file": ("forensic_mixed.eml", raw, "message/rfc822")},
        )
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        case_id = payload["case_id"]
        evidence_id = payload["evidence_id"]

        # Report reflects persisted forensic records (hops, attachments, IOCs,
        # MIME, summary) and cites the persisted record ids for traceability.
        self.assertEqual(self.client.post(f"/api/reports/{case_id}/generate").status_code, 200)
        report = self.client.get(f"/api/reports/{case_id}").json()
        report_text = " ".join([
            report.get("executive_summary", ""),
            report.get("evidence_analysis", ""),
            report.get("identity_analysis", ""),
            report.get("infrastructure_analysis", ""),
            report.get("campaign_correlation", ""),
            report.get("attack_path", ""),
            report.get("confidence_and_limitations", ""),
            report.get("conclusion", ""),
        ])
        report_lower = report_text.lower()
        for expected in [
            "evidence contains 5 mime part",
            "2 attachment",
            "2 observed transmission hop",
            "invoice.pdf",
            "ledger.csv",
            "192.0.2.7",
            "192.0.2.8",
            "http://evil-quest.example.net/pay",
            "refund@paid-login.example.net",
            "56cd7a52d4dbc4af2f1e64a46b7fd199a4ec569b6dd86c20cd74b1bad746f5c1",
            "hop record",
            "attachment record",
            "observed received chain",
            "not established",
        ]:
            self.assertIn(expected, report_lower, expected)

        # Report must not invent forensic facts: no registration claims, no
        # threat-feed claims when none are recorded, no attacker identity.
        for unsupported in [
            "third-party smtp relay", "has been flagged in", "registered",
            "privacy proxy registration", "the attacker", "intentional impersonation",
        ]:
            self.assertNotIn(unsupported, report_lower, unsupported)

        # Copilot answers evidence questions strictly from persisted records.
        def ask(question):
            resp = self.client.post(f"/api/copilot/{case_id}/ask", json={"question": question})
            self.assertEqual(resp.status_code, 200)
            return resp.json()["content"].lower()

        attach_text = ask("What attachments are present?")
        for expected in ["invoice.pdf", "ledger.csv", "sha256", "attachment record"]:
            self.assertIn(expected, attach_text)
        self.assertNotIn("malicious", attach_text)

        chain_text = ask("Show me the Received chain")
        for expected in ["192.0.2.7", "192.0.2.8", "hop record"]:
            self.assertIn(expected, chain_text)
        self.assertNotIn("source ip is fake", chain_text)

        iocs_text = ask("What observables were extracted?")
        for expected in ["http://evil-quest.example.net/pay", "refund@paid-login.example.net"]:
            self.assertIn(expected, iocs_text)
        self.assertIn("not verdicts", iocs_text)

        ips_text = ask("What IPs were observed?")
        for expected in ["192.0.2.7", "192.0.2.8"]:
            self.assertIn(expected, ips_text)

        domain_text = ask("Tell me about the domains and whois for this email")
        for expected in ["evil-quest.example.net", "paid-login.example.net", "not established", "was not queried"]:
            self.assertIn(expected, domain_text)
        self.assertNotIn("recently registered", domain_text)
        self.assertNotIn("the attacker", domain_text)

        # Case-scoping: a different case must never leak this case's records.
        valid_raw = self.fixture.read_bytes()
        other = self.client.post(
            "/api/cases/upload",
            files={"file": ("valid.eml", valid_raw, "message/rfc822")},
        ).json()
        other_id = other["case_id"]
        self.assertEqual(self.client.get(f"/api/cases/{other_id}/attachments").json(), [])
        other_text = self.client.post(
            f"/api/copilot/{other_id}/ask",
            json={"question": "What attachments are present?"},
        ).json()["content"].lower()
        self.assertIn("no attachments", other_text)
        self.assertNotIn("invoice.pdf", other_text)

        # Mutability: deleting a persisted forensic row changes the responses.
        db = sqlite3.connect(test_db_path())
        deleted = db.execute(
            "DELETE FROM attachments WHERE evidence_id = ? AND filename = 'invoice.pdf'",
            (evidence_id,),
        ).rowcount
        deleted_mime = db.execute(
            "DELETE FROM mime_parts WHERE evidence_id = ? AND filename = 'invoice.pdf'",
            (evidence_id,),
        ).rowcount
        db.commit()
        db.close()
        self.assertEqual(deleted, 1)
        self.assertEqual(deleted_mime, 1)

        attachments = self.client.get(f"/api/cases/{case_id}/attachments").json()
        self.assertEqual([a["filename"] for a in attachments], ["ledger.csv"])
        summary = self.client.get(f"/api/cases/{case_id}/forensic-summary").json()
        self.assertEqual(summary["attachments"], 1)

        self.assertEqual(self.client.post(f"/api/reports/{case_id}/generate").status_code, 200)
        report2 = self.client.get(f"/api/reports/{case_id}").json()
        text2 = " ".join([report2.get("evidence_analysis", ""), report2.get("executive_summary", "")])
        self.assertNotIn("invoice.pdf", text2)
        self.assertIn("ledger.csv", text2)
        self.assertIn("1 attachment", text2.lower())

        remove_text = self.client.post(
            f"/api/copilot/{case_id}/ask",
            json={"question": "What attachments are present?"},
        ).json()["content"].lower()
        self.assertNotIn("invoice.pdf", remove_text)
        self.assertIn("ledger.csv", remove_text)


if __name__ == "__main__":
    unittest.main()
