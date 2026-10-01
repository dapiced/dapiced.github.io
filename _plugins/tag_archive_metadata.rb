Jekyll::Hooks.register :site, :pre_render do |site, _payload|
  site.pages.each do |page|
    next unless page.data["layout"] == "tag-archive"

    tag = File.basename(page.url.chomp("/"))
    page.data["description"] = "Authored blog posts tagged ##{tag}."
  end
end
