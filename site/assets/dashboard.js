(() => {
  "use strict";

  const rows = [...document.querySelectorAll("[data-candidate-row]")];
  const search = document.querySelector("#candidate-search");
  const source = document.querySelector("#source-filter");
  const thesisOnly = document.querySelector("#thesis-filter");
  const count = document.querySelector("#visible-count");
  const emptyState = document.querySelector("#empty-state");
  const thesisData = JSON.parse(document.querySelector("#thesis-data").textContent);

  const applyFilters = () => {
    const query = search.value.trim().toLocaleLowerCase();
    let visible = 0;
    rows.forEach((row) => {
      const searchMatch = row.dataset.search.toLocaleLowerCase().includes(query);
      const sourceMatch = source.value === "all" || row.dataset.source === source.value;
      const thesisMatch = !thesisOnly.checked || row.dataset.thesisMatch === "true";
      const show = searchMatch && sourceMatch && thesisMatch;
      row.hidden = !show;
      if (show) visible += 1;
    });
    count.textContent = visible;
    emptyState.hidden = visible !== 0;
  };

  search.addEventListener("input", applyFilters);
  source.addEventListener("change", applyFilters);
  thesisOnly.addEventListener("change", applyFilters);

  const dialog = document.querySelector("#thesis-dialog");
  document.querySelector("#show-thesis").addEventListener("click", () => {
    dialog.showModal();
  });
  document.querySelector("#close-thesis").addEventListener("click", () => {
    dialog.close();
  });
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });

  document.documentElement.style.setProperty(
    "--thesis-sector-count",
    thesisData.sectors.length,
  );
})();
