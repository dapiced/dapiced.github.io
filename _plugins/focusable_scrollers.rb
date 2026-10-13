# frozen_string_literal: true

# Wide tables and code blocks in articles scroll horizontally
# (`overflow-x: auto` in style.css). A scrollable region must be reachable with
# the keyboard (WCAG 2.1.1, axe rule "scrollable-region-focusable"), so every
# <table> and <pre> in an article gets tabindex="0" at build time: no
# JavaScript needed, and authors keep writing plain Markdown.
module FocusableScrollers
  ARTICLE_LAYOUTS = %w[post portfolio apod].freeze
  SCROLLERS = /<(table|pre)(?![^>]*\btabindex=)/.freeze

  def self.apply(doc)
    return unless ARTICLE_LAYOUTS.include?(doc.data["layout"])
    return unless doc.output&.match?(SCROLLERS)

    doc.output = doc.output.gsub(SCROLLERS, '<\1 tabindex="0"')
  end
end

Jekyll::Hooks.register [:posts, :documents], :post_render do |doc|
  FocusableScrollers.apply(doc)
end
