# frozen_string_literal: true

# Open Graph expects a full locale (fr_CA, en_CA); jekyll-seo-tag falls back to
# the bare `lang` ("fr", "en"). Give every page and document a Canadian locale
# derived from its language, unless its front matter sets `locale` itself.
module PageLocale
  LOCALES = { "fr" => "fr_CA", "en" => "en_CA" }.freeze

  def self.apply(item, site)
    return if item.data["locale"]

    lang = (item.data["lang"] || site.config["lang"] || "en").to_s[0, 2]
    item.data["locale"] = LOCALES.fetch(lang, "en_CA")
  end
end

Jekyll::Hooks.register :site, :pre_render do |site, _payload|
  site.pages.each { |page| PageLocale.apply(page, site) }
  site.documents.each { |doc| PageLocale.apply(doc, site) }
end
