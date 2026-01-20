const API = "https://www.trans4trans.win:8003";

// List posts
if (document.location.pathname.endsWith("index.html") || document.location.pathname === "/") {
  fetch(API + "/posts")
    .then(res => res.json())
    .then(posts => {
      const el = document.getElementById("posts");
      posts.forEach(p => {
        el.innerHTML += `
          <div class="post">
            <a href="view.html?ts=${p.timestamp}">
              <h2>${p.title}</h2>
            </a>
            <small>${p.timestamp} — ${p.persona}</small>
          </div>
        `;
      });
    });
}

// View one post
if (document.location.pathname.endsWith("view.html")) {
  const ts = new URLSearchParams(location.search).get("ts");
  fetch(API + "/posts/" + ts)
    .then(res => res.json())
    .then(p => {
      document.getElementById("entry").innerHTML = `
        <h1>${p.title}</h1>
        <small>${p.timestamp} — ${p.persona}</small>
        <p>${p.content.replace(/\n/g, "<br>")}</p>
      `;
    });
}

// Submit entry
function submitEntry() {
  const title = document.getElementById("title").value;
  const content = document.getElementById("content").value;
  const key = document.getElementById("key").value;
  const persona = document.getElementById("persona").value;

  fetch(API + "/new?title=" + encodeURIComponent(title)
    + "&content=" + encodeURIComponent(content)
    + "&persona=" + encodeURIComponent(persona),
  {
    method: "POST",
    headers: {
      "X-Admin-Key": key
    }
  })
  .then(res => res.json())
  .then(r => {
    if (r.status === "ok") {
      location.href = "view.html?ts=" + r.timestamp;
    } else {
      alert("Error: " + JSON.stringify(r));
    }
  });
}
