document.addEventListener("DOMContentLoaded", function () {
  const perPage = 12;
  const container = document.querySelector(".home-categories");
  if (!container) return;

  const cards = Array.from(container.querySelectorAll(".post-card"));
  if (!cards.length) return;

  const totalPages = Math.ceil(cards.length / perPage);
  let currentPage = 1;

  function showPage(page) {
    // ограничиваем границы
    if (page < 1) page = 1;
    if (page > totalPages) page = totalPages;
    currentPage = page;

    cards.forEach((card, i) => {
      card.style.display =
        i >= (page - 1) * perPage && i < page * perPage ? "" : "none";
    });

    const buttons = container.querySelectorAll(".cat-page-btn");
    buttons.forEach(btn => {
      btn.classList.toggle("active", parseInt(btn.dataset.page) === page);
    });

    // состояние стрелок
    const prev = container.querySelector(".cat-prev");
    const next = container.querySelector(".cat-next");
    if (prev) prev.classList.toggle("disabled", currentPage === 1);
    if (next) next.classList.toggle("disabled", currentPage === totalPages);
  }

  // убираем старый пагинатор при hot reload
  const oldNav = container.querySelector("nav.pagination.cat-pagination");
  if (oldNav) oldNav.remove();

  if (totalPages > 1) {
    const nav = document.createElement("nav");
    nav.className = "pagination cat-pagination";

    // Prev
    const prev = document.createElement("a");
    prev.href = "#";
    prev.textContent = "« Prev";
    prev.className = "cat-prev";
    prev.addEventListener("click", e => {
      e.preventDefault();
      if (currentPage > 1) {
        showPage(currentPage - 1);
        container.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    });
    nav.appendChild(prev);

    // numbered buttons
    for (let i = 1; i <= totalPages; i++) {
      const a = document.createElement("a");
      a.href = "#";
      a.dataset.page = i;
      a.textContent = i;
      a.className = "cat-page-btn";
      a.addEventListener("click", e => {
        e.preventDefault();
        showPage(i);
        container.scrollIntoView({ behavior: "smooth", block: "start" });
      });
      nav.appendChild(a);
    }

    // Next
    const next = document.createElement("a");
    next.href = "#";
    next.textContent = "Next »";
    next.className = "cat-next";
    next.addEventListener("click", e => {
      e.preventDefault();
      if (currentPage < totalPages) {
        showPage(currentPage + 1);
        container.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    });
    nav.appendChild(next);

    container.appendChild(nav);
  }

  showPage(1);
});
