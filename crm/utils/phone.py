# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _


def normalize_mobile_no(value: str, label: str = "Mobile No.") -> str | None:
	"""
	Accept only a real phone number and return it in a clean, consistent form.

	Indian numbers (10 digits, or 10 digits behind a 91/+91 country code) must
	start with 6-9 and are normalised to "+91XXXXXXXXXX". Any other country code
	is kept as typed, as long as it looks like a phone number (8-15 digits).

	Empty values are returned as None and left to the usual mandatory checks.
	"""
	if not value:
		return None

	raw = value.strip()

	# Drop the "+" and the usual separators people type.
	digits = re.sub(r"\D", "", raw)

	if not digits:
		frappe.throw(_("{0} must be a valid phone number").format(_(label)), title=_("Invalid Mobile No."))

	# Drop the trunk prefix people type before a national number.
	digits = digits.lstrip("0") or digits

	# Figure out whether this is meant to be an Indian number. A bare 10-digit
	# number is one; so is anything behind a 91 country code. Note that a valid
	# national number can itself start with "91" (e.g. 9123456789), which is why
	# the 10-digit case is checked first.
	national = None
	if len(digits) == 10:
		national = digits
	elif digits.startswith("91"):
		national = digits[2:]

	if national is not None:
		if not re.fullmatch(r"[6-9]\d{9}", national):
			frappe.throw(
				_("{0} is not a valid mobile number. An Indian mobile number has 10 digits and starts with 6, 7, 8 or 9.").format(
					frappe.bold(raw)
				),
				title=_("Invalid Mobile No."),
			)
		return "+91" + national

	# Some other country code - just make sure it is plausible.
	if not 8 <= len(digits) <= 15:
		frappe.throw(
			_("{0} is not a valid phone number. Please enter the number with its country code.").format(
				frappe.bold(raw)
			),
			title=_("Invalid Mobile No."),
		)

	return "+" + digits
