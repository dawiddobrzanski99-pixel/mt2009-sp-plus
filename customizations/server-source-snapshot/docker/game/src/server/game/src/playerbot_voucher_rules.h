#ifndef __INC_METIN2_PLAYERBOT_VOUCHER_RULES_H__
#define __INC_METIN2_PLAYERBOT_VOUCHER_RULES_H__

// MT2009_PLUS_VOUCHER_CODES_V1 - the promo codes (the pure half, no engine).
//
// A code ("MT2009-PLUS-XXXX") is typed as "/kod <code>" (or "/voucher <code>");
// the case does not matter and spaces, dashes and underscores are dropped, so
// "mt2009 plus xxxx" and "MT2009PLUSXXXX" are the same code. The database
// keeps only SHA2(CONCAT(VOUCHER_SALT, <normalized code>), 256) - the hash
// lines of linux-port/docker/mariadb/playerbot/apply.sh, checked by
// linux-port/tools/test_vouchers.py, which also compiles this file.

#include <string>
#include <cstddef>

namespace mt2009_voucher_rules
{
	// Must equal the salt written in apply.sh's comment and test_vouchers.py.
	static const char* const VOUCHER_SALT = "MT2009PLUS|kody|v1|";

	// A normalized code is 1..MAX_CODE_LEN characters of [A-Z0-9].
	static const size_t MAX_CODE_LEN = 32;

	// The code as typed -> its normalized form; false (out empty) for a code
	// with any other character, an empty one or one too long.
	inline bool Normalize(const char* in, std::string& out)
	{
		out.clear();
		if (!in)
			return false;
		for (const char* p = in; *p; ++p)
		{
			const unsigned char c = (unsigned char) *p;
			if (c == ' ' || c == '\t' || c == '-' || c == '_' || c == '\r' || c == '\n')
				continue;
			if (c >= 'a' && c <= 'z')
				out += (char) (c - 'a' + 'A');
			else if ((c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9'))
				out += (char) c;
			else
			{
				out.clear();
				return false;
			}
			if (out.size() > MAX_CODE_LEN)
			{
				out.clear();
				return false;
			}
		}
		return !out.empty();
	}
}

#endif
