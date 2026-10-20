/* Local BM25 retrieval. No network requests, embeddings, or implied novelty judgment. */
(function (root) {
  const stop = new Set('a an the is it this that to of for on in with and or we i have has had tried try could would can does do what if using use'.split(' '));
  function tokens(text) {
    return (String(text).toLowerCase().replace(/[–—_]/g, '-').match(/[\p{L}\p{N}]+/gu) || []).filter(t => !stop.has(t));
  }
  function body(record) {
    return [record.title, record.title, record.question, record.summary, ...record.tags,
      ...Object.values(record.scope).flat(), record.finding, record.limitations, record.article || ''].join(' ');
  }
  function search(records, query) {
    const terms = [...new Set(tokens(query))];
    if (!terms.length) return [];
    const documents = records.map(record => ({record, words: tokens(body(record))}));
    const average = documents.reduce((n, d) => n + d.words.length, 0) / (documents.length || 1) || 1;
    const frequency = new Map(terms.map(term => [term, documents.filter(d => d.words.includes(term)).length]));
    return documents.map(({record, words}) => {
      let score = 0;
      const matched = [];
      for (const term of terms) {
        const count = words.filter(word => word === term).length;
        if (!count) continue;
        matched.push(term);
        const df = frequency.get(term);
        const idf = Math.log(1 + (records.length - df + 0.5) / (df + 0.5));
        score += idf * count * 2.2 / (count + 1.2 * (0.25 + 0.75 * words.length / average));
      }
      return {record, score, matched};
    }).filter(result => result.score > 0).sort((a, b) => b.score - a.score || a.record.id.localeCompare(b.record.id));
  }
  const api = {search, tokens};
  if (typeof module !== 'undefined') module.exports = api;
  else root.ExperimentSearch = api;
})(globalThis);
