/* ================================================================
   HackProof app asset — a small, safe Markdown renderer for the
   course reader (mdview.html). Safety rule: the source is HTML-
   escaped FIRST, formatting is applied to the escaped text, and
   link targets are restricted to http(s), the app scheme, and
   relative paths. Course lessons are Sentinel's own content, but
   a renderer that starts by escaping never has to trust it.
   Covers what the lessons use: headings, paragraphs, bold/italic,
   inline code + fenced blocks, ordered/unordered lists,
   blockquotes, horizontal rules, links, and simple pipe tables.
   ================================================================ */
"use strict";

function hpEscapeHtml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;")
          .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function hpInline(s) {
  var out = s;
  out = out.replace(/`([^`]+)`/g, "<code>$1</code>");
  out = out.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  out = out.replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>");
  out = out.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, function (m, text, href) {
    if (/^(https?:\/\/|hackproof:|\/|\.\/|\.\.\/|#)/.test(href)) {
      return '<a href="' + href + '">' + text + "</a>";
    }
    return text;
  });
  return out;
}

function hpRenderMarkdown(source) {
  var lines = String(source || "").replace(/\r\n/g, "\n").split("\n");
  var html = [];
  var i = 0;
  var listType = null; // "ul" | "ol" | null
  function closeList() {
    if (listType) { html.push("</" + listType + ">"); listType = null; }
  }
  while (i < lines.length) {
    var line = lines[i];
    // Fenced code block
    var fence = line.match(/^```/);
    if (fence) {
      closeList();
      var buf = [];
      i++;
      while (i < lines.length && !/^```/.test(lines[i])) { buf.push(lines[i]); i++; }
      i++; // closing fence
      html.push("<pre><code>" + hpEscapeHtml(buf.join("\n")) + "</code></pre>");
      continue;
    }
    // Pipe table (header + separator row)
    if (/^\|.*\|$/.test(line.trim()) && i + 1 < lines.length &&
        /^\|[\s:|-]+\|$/.test(lines[i + 1].trim())) {
      closeList();
      var head = line.trim().slice(1, -1).split("|")
        .map(function (c) { return "<th>" + hpInline(hpEscapeHtml(c.trim())) + "</th>"; });
      html.push("<table><thead><tr>" + head.join("") + "</tr></thead><tbody>");
      i += 2;
      while (i < lines.length && /^\|.*\|$/.test(lines[i].trim())) {
        var cells = lines[i].trim().slice(1, -1).split("|")
          .map(function (c) { return "<td>" + hpInline(hpEscapeHtml(c.trim())) + "</td>"; });
        html.push("<tr>" + cells.join("") + "</tr>");
        i++;
      }
      html.push("</tbody></table>");
      continue;
    }
    var heading = line.match(/^(#{1,6})\s+(.*)$/);
    if (heading) {
      closeList();
      var level = heading[1].length;
      html.push("<h" + level + ">" + hpInline(hpEscapeHtml(heading[2])) +
                "</h" + level + ">");
      i++;
      continue;
    }
    if (/^\s*(-{3,}|\*{3,})\s*$/.test(line)) {
      closeList(); html.push("<hr>"); i++; continue;
    }
    var quote = line.match(/^>\s?(.*)$/);
    if (quote) {
      closeList();
      html.push("<blockquote>" + hpInline(hpEscapeHtml(quote[1])) + "</blockquote>");
      i++;
      continue;
    }
    var ul = line.match(/^\s*[-*]\s+(.*)$/);
    var ol = line.match(/^\s*\d+[.)]\s+(.*)$/);
    if (ul || ol) {
      var type = ul ? "ul" : "ol";
      if (listType !== type) { closeList(); html.push("<" + type + ">"); listType = type; }
      html.push("<li>" + hpInline(hpEscapeHtml((ul || ol)[1])) + "</li>");
      i++;
      continue;
    }
    if (/^\s*$/.test(line)) { closeList(); i++; continue; }
    // Paragraph: gather until a blank line or a block construct.
    closeList();
    var para = [line];
    i++;
    while (i < lines.length && !/^\s*$/.test(lines[i]) &&
           !/^(#{1,6}\s|```|>|\s*[-*]\s|\s*\d+[.)]\s)/.test(lines[i])) {
      para.push(lines[i]); i++;
    }
    html.push("<p>" + hpInline(hpEscapeHtml(para.join(" "))) + "</p>");
  }
  closeList();
  return html.join("\n");
}
