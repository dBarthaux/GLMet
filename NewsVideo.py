
import webbrowser
import os


# =============================================================================
# 
# =============================================================================

def create_video_ticker(textcrawl, video_id="73-EekdVVU8"):
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
body {{
  margin: 0;
  overflow: hidden;
  background: black;
}}
iframe {{
  width: 100vw;
  height: 100vh;
  z-index: 0;
  position: relative;
}}
#ticker {{
  position: fixed;
  bottom: 0;
  height: 50px;
  line-height: 17.5px;
  width: 100%;
  background: rgba(0,0,0,0.9);
  color: white;
  font-size: 36px;
  white-space: pre;   /* <-- preserve tabs and spacing */
  overflow: hidden;
  z-index: 9999;
}}
#ticker span {{
  display: inline-block;
  padding-left: 100%;
  animation: scroll linear infinite;
}}
@keyframes scroll {{
  from {{ transform: translateX(0%); }}
  to {{ transform: translateX(-100%); }}
}}
</style>
</head>
<body>
<iframe src="https://www.youtube.com/embed/{video_id}?autoplay=1&mute=1&controls=0&modestbranding=1&rel=0" 
        frameborder="0" allow="autoplay; fullscreen"></iframe>

<div id="ticker"><span>
{textcrawl}
</span></div>

<script>
window.onload = function() {{
  const span = document.querySelector("#ticker span");
  const speed = 120; // pixels per second
  const textWidth = span.offsetWidth;
  const duration = textWidth / speed;
  span.style.animationDuration = duration + "s";
}};
</script>
</body>
</html>
"""
    filename = "video_ticker.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)

    # open in default browser
    webbrowser.open('file://' + os.path.realpath(filename))

if __name__ == "__main__":
    textcrawl = open('TextCrawl.txt').read()
    create_video_ticker(textcrawl)
