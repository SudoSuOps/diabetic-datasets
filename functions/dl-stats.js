// GET /dl-stats — public read of the download record (counts per dataset, total, by day, by country).
// Reads the same KV namespace `DL` the /dl/<slug> redirect writes to. Fail-open: returns {} if unbound.
export async function onRequest(context) {
  const { env } = context;
  const out = { total: 0, datasets: {}, days: {}, countries: {} };
  try {
    if (env.DL) {
      let cursor;
      do {
        const list = await env.DL.list({ cursor });
        for (const k of list.keys) {
          const v = Number((await env.DL.get(k.name)) || 0);
          if (k.name === "count:_total") out.total = v;
          else if (k.name.startsWith("count:")) out.datasets[k.name.slice(6)] = v;
          else if (k.name.startsWith("day:")) out.days[k.name.slice(4)] = v;
          else if (k.name.startsWith("country:")) out.countries[k.name.slice(8)] = v;
        }
        cursor = list.cursor;
      } while (cursor);
    }
  } catch (e) { /* fail-open */ }
  return new Response(JSON.stringify(out, null, 1), {
    headers: { "content-type": "application/json", "cache-control": "max-age=60" },
  });
}
