import webbrowser
import os

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
}}
#ticker {{
  position: fixed;
  bottom: 0;
  width: 100%;
  background: rgba(0,0,0,0.7);
  color: white;
  font-size: 36px;
  white-space: nowrap;
  overflow: hidden;
}}
#ticker span {{
  display: inline-block;
  padding-left: 100%;
  animation: scroll 20s linear infinite;
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
</body>
</html>
"""
    filename = "video_ticker.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)

    # open in default browser
    webbrowser.open('file://' + os.path.realpath(filename))

if __name__ == "__main__":
    create_video_ticker()
