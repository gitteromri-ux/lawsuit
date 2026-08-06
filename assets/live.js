/* Reads cases filed through the form straight from the public issue API and shows them
   instantly, without waiting for any build step. The static pages stay the permanent record;
   this only makes a freshly filed case visible the moment it is submitted. */
(function () {
  var API = "https://api.github.com/repos/gitteromri-ux/lawsuit/issues?labels=case&state=all&per_page=100";
  var CAT = {
    "missed eta": "Missed ETA",
    "false status claim": "False status claim",
    "scope reduced": "Scope reduced",
    "started with no approved eta": "Started with no approved ETA",
    "asked for an extension": "Asked for an extension",
    "audit claimed, defect found": "Audit claimed, defect found",
    "broken or missing deliverable": "Broken or missing deliverable",
    "compute waste, billed to me": "Compute waste, billed to client",
    "directions instead of a deep link": "Directions instead of deep link",
    "other rule breach": "Other rule breach"
  };

  function parseForm(body) {
    var out = {}, re = /^###[ \t]+(.+?)[ \t]*\n+([\s\S]*?)(?=\n###[ \t]|$)/gm, m;
    while ((m = re.exec(body || ""))) out[m[1].trim().toLowerCase()] = m[2].trim();
    return out;
  }
  function blank(v) {
    if (!v) return true;
    var s = v.trim().toLowerCase();
    return s === "_no response_" || s === "n/a" || s === "none" || s === "-";
  }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function toCase(issue) {
    var f = parseForm(issue.body);
    var sum = f["what happened"] || issue.title.replace(/^CASE:\s*/i, "");
    if (!sum) return null;
    var sev = 3, sm = /([1-5])/.exec(f["how bad"] || "");
    if (sm) sev = parseInt(sm[1], 10);
    var aq = blank(f["what the agent said, copied exactly"]) ? "" : f["what the agent said, copied exactly"];
    var cq = blank(f["what you said, copied exactly"]) ? "" : f["what you said, copied exactly"];
    var thread = blank(f["thread link or session id"]) ? "" : f["thread link or session id"].trim();
    var d = f["date"] && /^\d{4}-\d{2}-\d{2}$/.test(f["date"].trim())
      ? f["date"].trim() : issue.created_at.slice(0, 10);
    return {
      id: "I-" + String(issue.number).padStart(3, "0"),
      n: issue.number,
      summary: sum,
      cat: CAT[(f["what kind of failure"] || "").trim().toLowerCase()] || "Other rule breach",
      sev: sev,
      project: f["which project"] || "Other",
      date: d,
      time: issue.created_at.slice(11, 16),
      agent: aq, client: cq, thread: thread,
      minutes: /^\d+$/.test((f["minutes lost"] || "").trim()) ? f["minutes lost"].trim() : "",
      url: issue.html_url,
      proven: aq ? "PROVEN" : "ALLEGED"
    };
  }

  function article(c) {
    var q = "";
    if (c.agent) q += '<div class="q agent"><b>AGENT, VERBATIM</b>' + esc(c.agent) + "</div>";
    if (c.client) q += '<div class="q client"><b>CLIENT, VERBATIM</b>' + esc(c.client) + "</div>";
    var links = '<a class="lnk" href="' + esc(c.url) + '" target="_blank" rel="noopener">The filing</a>';
    if (c.thread) links += '<a class="lnk" href="' + esc(c.thread) + '" target="_blank" rel="noopener">Open the transcript</a>';
    return '<article class="case s' + c.sev + '" data-cat="LIVE" data-sev="' + c.sev + '">' +
      '<div class="crow"><span class="cid">' + esc(c.id) + '</span>' +
      '<span class="badge cat">' + esc(c.cat) + "</span>" +
      '<span class="badge sev">Severity ' + c.sev + "/5</span>" +
      '<span class="badge pf' + (c.proven === "PROVEN" ? "" : " alleged") + '">' + c.proven + "</span>" +
      '<span class="badge pj">' + esc(c.project) + "</span>" +
      '<span class="cid">' + esc(c.date) + " · " + esc(c.time) + " UTC</span>" +
      '<span class="badge vq">FILED BY YOU</span></div>' +
      "<h3>" + esc(c.summary) + "</h3>" + q +
      '<div class="cfoot">' + links +
      (c.minutes ? '<span>Minutes lost: <b style="color:#E9C46A">' + esc(c.minutes) + "</b></span>" : "") +
      "</div></article>";
  }

  function row(c) {
    return "<tr><td><b>" + esc(c.id) + "</b></td><td>" + esc(c.date) + "</td><td>" + esc(c.cat) +
      "</td><td>" + c.sev + "/5</td><td>" + esc(c.project) +
      '</td><td><a class="lnk" href="' + esc(c.url) + '" target="_blank" rel="noopener">The filing</a></td></tr>';
  }

  fetch(API, { headers: { Accept: "application/vnd.github+json" } })
    .then(function (r) { return r.ok ? r.json() : []; })
    .then(function (list) {
      var cases = (list || []).map(toCase).filter(Boolean)
        .sort(function (a, b) { return b.n - a.n; });
      if (!cases.length) return;

      var banner = document.createElement("div");
      banner.className = "note";
      banner.innerHTML = "<b>" + cases.length + " case" + (cases.length > 1 ? "s" : "") +
        " filed through the form.</b> Shown live, straight from your filings. They are folded " +
        "into the permanent dataset and the charts on the next rebuild.";

      var list1 = document.getElementById("caselist");
      if (list1) {
        list1.insertAdjacentHTML("afterbegin", cases.map(article).join(""));
        list1.parentNode.insertBefore(banner, list1.previousElementSibling || list1);
      }
      var tbl = document.querySelector(".dl-table tbody");
      if (tbl) {
        tbl.insertAdjacentHTML("afterbegin", cases.map(row).join(""));
        var dl = document.querySelector(".big-dl");
        if (dl) dl.parentNode.insertBefore(banner, dl);
      }
      var chip = document.querySelector(".chips .chip .n");
      if (chip) {
        var base = parseInt(chip.textContent, 10);
        if (!isNaN(base)) {
          chip.textContent = base + cases.length;
          var lbl = chip.parentNode.querySelector(".l");
          if (lbl && lbl.textContent.indexOf("filed") === -1) {
            lbl.textContent = lbl.textContent + ", including " + cases.length + " you filed";
          }
        }
      }
    })
    .catch(function () { /* the static record stands on its own */ });
})();
