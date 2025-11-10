    fm = (
        "---\n"
        f'title: "{_title_case(longtail)}"\n'
        f"date: {now.isoformat()}\n"
        "draft: false\n"
        f'slug: "{safe_slug}"\n'
        f"categories: ['{cat.name}']\n"
        f"tags: [{', '.join([f'\"{t}\"' for t in auto_tags])}]\n"
        f'author: "{author_name}"\n'
        f'image: "{image_url}"\n'
    )
    if meta_desc:
        fm += f'description: "{meta_desc}"\n'
    fm += "---\n\n"

    with out_path.open('w', encoding='utf-8') as f:
        f.write(fm + article_md.strip() + "\n")

    print(f"[eQualle SAVE][OK] ✅ {out_path}")
    record_used_pair(state_path, seed, longtail)
    _ci_persist_author_state(data_dir)
    print("[eQualle DONE] 🎉 All steps completed successfully.")


if __name__ == "__main__":
    main()
