from app.services.discovery.engine import scan_text, score_finding


def test_detects_aws_and_stripe():
    sample = """
    AWS_ACCESS_KEY_ID=AKIAEXAMPLEKEY000000
    STRIPE=sk_test_51Habcdefghijklmnopqrstuvwx
    token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U
    -----BEGIN RSA PRIVATE KEY-----
    MIIEowIBAAKCAQEA0Z3VS5JJcds3xfn
    """
    findings = scan_text(sample, "app.env")
    types = {f.secret_type for f in findings}
    assert "aws_access_key" in types
    assert "stripe_key" in types
    assert "jwt" in types
    assert "ssh_private_key" in types
    scored = score_finding(findings[0])
    assert scored["risk_score"] > 0
    assert "value_encrypted" in scored
    assert scored["snippet_redacted"]
