# frozen_string_literal: true

require "digest"

# Content-based cache busting for local assets.
#
#   <link rel="stylesheet" href="{{ '/assets/css/style.css' | asset_digest }}">
#   => /assets/css/style.css?v=3f2a9c1b7d4e
#
# The query string only changes when the file content changes, so browsers and
# the Cloudflare edge can cache assets for a long time while a new deployment
# still reaches every visitor. The previous `?v={{ site.time }}` changed on
# every build, which invalidated the CSS even when it was untouched.
module AssetDigest
  DIGEST_LENGTH = 12

  def asset_digest(path)
    site = @context.registers[:site]
    source = File.join(site.source, path.to_s.sub(%r{\A/}, ""))
    unless File.file?(source)
      raise ArgumentError, "asset_digest: #{path} does not exist in the site source"
    end

    "#{path}?v=#{Digest::SHA256.file(source).hexdigest[0, DIGEST_LENGTH]}"
  end

  # Short digest of a string, e.g. the service worker's shell list (sw.js).
  def text_digest(input)
    Digest::SHA256.hexdigest(input.to_s)[0, DIGEST_LENGTH]
  end
end

Liquid::Template.register_filter(AssetDigest)
