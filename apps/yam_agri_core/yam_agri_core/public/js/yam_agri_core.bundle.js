(() => {
	const path = window.location.pathname || "";
	if (!path.startsWith("/desk/")) {
		return;
	}

	const match = path.match(/^\/desk\/([^/]+)(?:\/view\/list)?\/?$/i);
	if (!match || !match[1]) {
		return;
	}

	const firstSegment = decodeURIComponent(match[1]);
	const reservedDeskPages = new Set([
		"workspace",
		"modules",
		"list",
		"Form",
		"report",
		"query-report",
		"print",
		"background_jobs",
		"backups",
		"users",
		"role",
		"setup-wizard",
	]);
	if (reservedDeskPages.has(firstSegment)) {
		return;
	}

	const appRoute = `/app/${firstSegment.toLowerCase()}`;
	if (window.location.pathname !== appRoute) {
		window.location.replace(appRoute + window.location.search + window.location.hash);
	}
})();
