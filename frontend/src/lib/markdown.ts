// Minimal, dependency-free Markdown renderer for a safe subset.
// HTML is escaped first, so the output is safe to use with {@html} even for
// untrusted input. Supports: #/##/### headings, **bold**, *italic*, `code`,
// [text](url) links, unordered/ordered lists, blockquotes, and paragraphs.

function escapeHtml(s: string): string {
	return s
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')
		.replace(/"/g, '&quot;');
}

function inline(text: string): string {
	return text
		.replace(/`([^`]+)`/g, (_m, c) => `<code>${c}</code>`)
		.replace(/\*\*([^*]+)\*\*/g, (_m, c) => `<strong>${c}</strong>`)
		.replace(/\*([^*]+)\*/g, (_m, c) => `<em>${c}</em>`)
		.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, (_m, t, u) => `<a href="${u}" target="_blank" rel="noopener">${t}</a>`);
}

export function renderMarkdown(src: string): string {
	const lines = escapeHtml(src ?? '').split('\n');
	const html: string[] = [];
	let listType: 'ul' | 'ol' | null = null;
	let paragraph: string[] = [];

	const flushParagraph = () => {
		if (paragraph.length) {
			html.push(`<p>${inline(paragraph.join(' '))}</p>`);
			paragraph = [];
		}
	};
	const closeList = () => {
		if (listType) {
			html.push(`</${listType}>`);
			listType = null;
		}
	};

	for (const raw of lines) {
		const line = raw.trimEnd();

		if (!line.trim()) {
			flushParagraph();
			closeList();
			continue;
		}

		const heading = line.match(/^(#{1,3})\s+(.*)$/);
		if (heading) {
			flushParagraph();
			closeList();
			const level = heading[1].length;
			html.push(`<h${level}>${inline(heading[2])}</h${level}>`);
			continue;
		}

		if (/^>\s?/.test(line)) {
			flushParagraph();
			closeList();
			html.push(`<blockquote>${inline(line.replace(/^>\s?/, ''))}</blockquote>`);
			continue;
		}

		const ul = line.match(/^[-*]\s+(.*)$/);
		const ol = line.match(/^\d+\.\s+(.*)$/);
		if (ul || ol) {
			flushParagraph();
			const type = ul ? 'ul' : 'ol';
			if (listType !== type) {
				closeList();
				html.push(`<${type}>`);
				listType = type;
			}
			html.push(`<li>${inline((ul ?? ol)![1])}</li>`);
			continue;
		}

		closeList();
		paragraph.push(line.trim());
	}

	flushParagraph();
	closeList();
	return html.join('\n');
}
