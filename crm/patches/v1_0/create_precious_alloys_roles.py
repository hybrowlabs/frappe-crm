from crm.install import add_precious_alloys_roles


def execute():
	"""Create the Precious Alloys dashboard business roles (CEO, Technical Head,
	Technical Person, Marketing Team) on existing sites. Idempotent — skips any
	role that already exists."""
	add_precious_alloys_roles()
