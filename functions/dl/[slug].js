// Cloudflare Pages Function — GET /dl/<slug>
// Records the download (count per dataset + total) then 302-redirects to the real Tigris URL.
// Fail-open: a download NEVER breaks because logging hiccupped. The catalog keeps the true
// Tigris URLs (for the SHA verify widget); only the download button/CLI route through here so
// we have a record of what the community actually pulls.
//
// v2 — DL KV binding active. Storage binding (optional but recommended): a KV namespace bound as `DL` in the Pages project.
//   Cloudflare Pages → Settings → Functions → KV namespace bindings → Variable name: DL
// Without it, downloads still work; they just aren't counted.

export async function onRequest(context) {
  const { params, env, request } = context;
  const slug = (params.slug || "").toString();

  // resolve the real download URL from the catalog (same origin)
  let url = null;
  try {
    const cat = await (await fetch(new URL("/catalog.json", request.url))).json();
    const items = Array.isArray(cat) ? cat : (cat.datasets || []);
    const ds = items.find((d) => d.slug === slug);
    url = (ds && (ds.full_download?.url || ds.sample_download)) || null;
  } catch (e) { /* fall through to 404 */ }

  if (!url) return new Response("Unknown dataset.", { status: 404 });

  // record the download — fail-open
  try {
    if (env.DL) {
      const country = request.headers.get("cf-ipcountry") || "??";
      const day = new Date().toISOString().slice(0, 10);
      const bump = async (k) => env.DL.put(k, String(1 + Number((await env.DL.get(k)) || 0)));
      context.waitUntil(Promise.all([
        bump(`count:${slug}`),
        bump(`count:_total`),
        bump(`day:${day}`),
        bump(`country:${country}`),
      ]));
    }
  } catch (e) { /* never block the download */ }

  return Response.redirect(url, 302);
}
