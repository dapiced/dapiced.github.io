# frozen_string_literal: true

# Points og:image / twitter:image at the share card drawn by
# tools/og-cards/og_cards.py (assets/img/og/<slug>.jpg) when one exists for a
# post or portfolio entry. The front matter `image` stays the source of truth
# for the card's photo; only the copy jekyll-seo-tag reads is replaced.
module OgCards
  DIR = "assets/img/og"

  def self.slug(doc)
    base = File.basename(doc.path, ".*")
    doc.collection.label == "posts" ? base.sub(/\A\d{4}-\d{2}-\d{2}-/, "") : base
  end

  def self.apply(doc, site)
    card = File.join(DIR, "#{slug(doc)}.jpg")
    return unless File.file?(File.join(site.source, card))

    doc.data["image"] = {
      "path" => "/#{card}",
      "width" => 1200,
      "height" => 630,
      "alt" => doc.data["title"].to_s,
    }
  end
end

Jekyll::Hooks.register :site, :post_read do |site|
  %w[posts portfolio].each do |label|
    collection = site.collections[label]
    collection&.docs&.each { |doc| OgCards.apply(doc, site) }
  end
end
