export default {
  title: "CWC flood forecast system",
  root: "src",
  // GitHub Pages serves a project site under /<repository>/. Set this to "/"
  // if you move the site to a custom domain.
  base: "/cwc-flood-forecasts/",
  style: "style.css",
  header: "",
  footer: `Scraped from the Central Water Commission Flood Forecast System portal.
    Download the data as CSV or Parquet from
    <a href="https://github.com/diagram-chasing/cwc-flood-forecasts">github.com/diagram-chasing/cwc-flood-forecasts</a>.`,
  toc: false,
  sidebar: false,
  pager: false,
  search: false,
  head: `<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Ctext y='14' font-size='14'%3E%F0%9F%8C%8A%3C/text%3E%3C/svg%3E">`,
  // The Python loaders run in the dataset's own uv environment, one directory up.
  interpreters: {
    ".py": ["uv", "run", "--quiet", "--project", "..", "python"]
  }
};
