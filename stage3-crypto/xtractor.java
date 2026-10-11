import java.util.Base64;

void main(String[] args) {
	if (args.length != 2) {
		IO.println("""
			xtractor <clear_text> <base64_text>
			Script to XOR the given clear-text against the given base64 (decoded) text.
			""");
		System.exit(1);
	}

	IO.println("Clear Text: " + args[0]);
	IO.println("Base64 Text: " + args[1]);

	final var b64d = Base64.getDecoder();
	final byte[] b64Bytes = b64d.decode(args[1]);
	final byte[] clrBytes = args[0].getBytes();

	final byte[] xoredBytes = new byte[b64Bytes.length];
	int j = 0;
	for (int i = 0; i < b64Bytes.length; i++) {
		if (j == clrBytes.length) j = 0;
		xoredBytes[i] = (byte) (clrBytes[j++] ^ b64Bytes[i]);
	}

	IO.println("XORed Text: " + new String(xoredBytes));
}
