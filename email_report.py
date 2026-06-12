import html


def _badge(text, color, background):
    return (
        f'<span style="display:inline-block;padding:2px 10px;border-radius:12px;'
        f'font-size:12px;font-weight:600;color:{color};background:{background};">{text}</span>'
    )


def _cell_html(result):
    if result.get("no_items"):
        return '<p style="margin:0;font-size:13px;color:#666;">No items currently borrowed.</p>'

    currently_borrowing = result["currently_borrowing"]
    renewed_count = result["renewed_count"]
    must_return = result.get("must_return", [])

    renewed_badge = _badge(
        f"{renewed_count} renewed" if renewed_count else "none renewed",
        "#1e7e34" if renewed_count else "#666",
        "#e6f4ea" if renewed_count else "#eee",
    )

    body = (
        f'<p style="margin:0 0 8px;font-size:14px;">'
        f'Currently borrowing <strong>{currently_borrowing}</strong>'
        f'&nbsp;&nbsp;{renewed_badge}</p>'
    )

    if must_return:
        rows = "".join(
            '<tr>'
            f'<td style="padding:6px 10px;border:1px solid #f5c6cb;font-size:13px;">{html.escape(b["title"])}</td>'
            f'<td style="padding:6px 10px;border:1px solid #f5c6cb;font-size:13px;white-space:nowrap;">{b["due_date"]}</td>'
            '</tr>'
            for b in must_return
        )
        body += (
            '<p style="margin:12px 0 4px;font-size:13px;font-weight:600;color:#a94442;">'
            '⚠️ Must return soon</p>'
            '<table role="presentation" style="width:100%;border-collapse:collapse;">'
            '<tr style="background:#fdecea;color:#a94442;">'
            '<th style="text-align:left;padding:6px 10px;border:1px solid #f5c6cb;font-size:12px;">Title</th>'
            '<th style="text-align:left;padding:6px 10px;border:1px solid #f5c6cb;font-size:12px;">Due date</th>'
            '</tr>'
            f'{rows}'
            '</table>'
        )
    else:
        body += '<p style="margin:12px 0 0;font-size:13px;color:#1e7e34;">Nothing due back soon</p>'

    return body


def build_html_report(results, today):
    # group into a grid: one row per library, one column per user, in order
    # of first appearance, so the layout is library x user regardless of the
    # order results were collected in
    libraries = []
    users = []
    grid = {}
    for r in results:
        if r["library"] not in libraries:
            libraries.append(r["library"])
        if r["user"] not in users:
            users.append(r["user"])
        grid[(r["library"], r["user"])] = r

    # the data columns (one per user) are 1.5x wider than the header column
    header_col_width = 100 / (1.5 * len(users) + 1) if users else 100
    data_col_width = header_col_width * 1.5

    header_style = (
        'padding:12px 16px;border:1px solid #eee;background:#eef1f5;'
        'font-size:13px;font-weight:600;color:#2d3e50;text-align:center;vertical-align:middle;'
    )
    data_style = 'padding:16px;border:1px solid #eee;vertical-align:top;'

    # header row: corner cell + one cell per user (column headers)
    corner_cell = f'<td style="width:{header_col_width:.4f}%;{header_style}"></td>'
    user_header_cells = "".join(
        f'<td style="width:{data_col_width:.4f}%;{header_style}">{html.escape(user)}</td>'
        for user in users
    )
    grid_rows = f'<tr>{corner_cell}{user_header_cells}</tr>'

    # one row per library: row header cell (library name) + one data cell per user
    for library in libraries:
        library_header_cell = f'<td style="width:{header_col_width:.4f}%;{header_style}">{html.escape(library)}</td>'
        data_cells = ""
        for user in users:
            result = grid.get((library, user))
            content = _cell_html(result) if result else ""
            data_cells += f'<td style="width:{data_col_width:.4f}%;{data_style}">{content}</td>'
        grid_rows += f'<tr>{library_header_cell}{data_cells}</tr>'

    return f"""\
<html>
  <body style="margin:0;padding:20px;background:#f4f4f7;font-family:Arial,Helvetica,sans-serif;color:#333;">
    <table role="presentation" style="max-width:600px;margin:0 auto;background:#ffffff;border-radius:8px;overflow:hidden;border:1px solid #e0e0e0;border-collapse:collapse;">
      <tr>
        <td style="background:#2d3e50;color:#ffffff;padding:20px 24px;">
          <p style="margin:0;font-size:18px;font-weight:600;">\U0001f4da Library Renewal Report</p>
          <p style="margin:4px 0 0;font-size:13px;opacity:0.8;">{today.strftime('%A, %d %B %Y')}</p>
        </td>
      </tr>
      <tr>
        <td style="padding:0;">
          <table role="presentation" style="width:100%;table-layout:fixed;border-collapse:collapse;">
            {grid_rows}
          </table>
        </td>
      </tr>
      <tr>
        <td style="padding:12px 24px;background:#f4f4f7;font-size:11px;color:#999;text-align:center;">
          Generated automatically
        </td>
      </tr>
    </table>
  </body>
</html>
"""


def build_text_report(results, today):
    lines = [f"Library Renewal Report - {today}", ""]
    for r in results:
        lines.append(f"{r['user']} - {r['library']}")
        if r.get("no_items"):
            lines.append("  No items currently borrowed.")
        else:
            lines.append(f"  Currently borrowing: {r['currently_borrowing']}")
            lines.append(f"  Renewed: {r['renewed_count']}")
            must_return = r.get("must_return", [])
            if must_return:
                lines.append("  Must return soon:")
                for b in must_return:
                    lines.append(f"    - {b['title']} (due {b['due_date']})")
            else:
                lines.append("  Nothing due back soon")
        lines.append("")
    return "\n".join(lines)
