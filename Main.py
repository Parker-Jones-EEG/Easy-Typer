import json, os, random, re, subprocess, threading, time, urllib.request, pyautogui, rumps

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0
CONFIG_PATH = os.path.expanduser("~/.dewey_typer_settings.json")
DEFAULTS = {"wpm": 95, "typo_rate": 0.8, "correction_rate": 3.5, "humanizer": True, "model": "llama3.2", "tone": "Natural Everyday"}

TONES = {
    "Natural Everyday": "Write in a relaxed, natural everyday human voice. Use contractions, vary sentence lengths, and keep it clear and conversational.",
    "Casual Student": "Write like a smart college student writing an essay or discussion post. Keep it approachable, authentic, and slightly informal without slang.",
    "Concise Pro": "Write like a busy human professional. Be clear, direct, and polite. Cut all fluff, filler words, and corporate buzzwords.",
    "Academic Clean": "Write in a thoughtful, well-structured academic tone that still sounds like a real human researcher—avoid robotic transitions and inflated vocabulary.",
    "Punchy Direct": "Use short, energetic, direct sentences. Make every word count and avoid passive voice or long wind-ups."
}

def load_cfg():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return {**DEFAULTS, **json.load(f)}
    except Exception:
        return DEFAULTS.copy()

def save_cfg(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f)
    except Exception:
        pass

def clean_chars(txt):
    for k, v in {"\u201c": '"', "\u201d": '"', "\u2018": "'", "\u2019": "'", "\u2014": " - ", "\u2013": "-", "\u2026": "...", "\u00a0": " "}.items():
        txt = txt.replace(k, v)
    return txt

def offline_humanize(txt):
    txt = clean_chars(txt)
    openers = [r"\bit is (important|worth) (to note|noting) that\s+", r"\bit's important to remember that\s+", r"\bin today's fast-paced world,?\s+", r"\bin the (ever-evolving landscape|realm) of\s+", r"\bwhen it comes to\s+", r"\b(needless to say|all things considered),?\s+"]
    for p in openers:
        txt = re.sub(p, "", txt, flags=re.I)
    txt = re.sub(r"(^|[.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), txt)
    swaps = {
        "it is crucial to": ["you really need to", "it's key to"], "not only": ["not just"], "but also": ["but", "and also"],
        "testament to": ["proof of", "evidence of"], "delving into": ["looking into", "digging into"], "delve into": ["look into", "dig into"],
        "furthermore": ["also", "plus"], "moreover": ["also", "besides that"], "in conclusion": ["overall", "to wrap up"],
        "subsequent": ["next", "following"], "essential": ["super important", "key"], "crucial": ["huge", "critical"],
        "utilizing": ["using"], "utilize": ["use"], "facilitate": ["help with", "make easier"], "implement": ["set up", "use"],
        "leverage": ["use", "take advantage of"], "comprehensive": ["full", "thorough"], "robust": ["strong", "solid"],
        "seamless": ["smooth", "easy"], "pivotal": ["major", "key"], "paramount": ["most important"], "myriad": ["tons of", "many"],
        "plethora": ["tons of", "plenty of"], "tapestry": ["mix", "blend"], "fostering": ["building", "encouraging"],
        "foster": ["build", "encourage"], "underscore": ["highlight", "show"], "remains": ["is still", "stays"],
        "therefore": ["so"], "cutting-edge": ["new", "modern"], "revolutionizing": ["changing", "reshaping"]
    }
    for ai, opts in swaps.items():
        def repl(m, o=opts):
            s, c = m.group(0), random.choice(o)
            return c.upper() if s.isupper() else (c.upper() + c[1:] if s.isupper() else c.lower())
        txt = re.sub(r"\b" + re.escape(ai) + r"\b", repl, txt, flags=re.I)
    contr = {"do not": "don't", "does not": "doesn't", "did not": "didn't", "cannot": "can't", "will not": "won't", "would not": "wouldn't", "is not": "isn't", "are not": "aren't", "it is": "it's", "that is": "that's", "they are": "they're", "we are": "we're", "you are": "you're", "I am": "I'm"}
    for f, c in contr.items():
        def c_repl(m, cas=c):
            if random.random() > 0.85: return m.group(0)
            s = m.group(0)
            return cas.upper() if s.isupper() else (cas.upper() + cas[1:] if s.isupper() else cas)
        txt = re.sub(r"\b" + re.escape(f) + r"\b", c_repl, txt, flags=re.I)
    return txt

def call_ollama(prompt, model="llama3.2", timeout=35):
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.85, "top_p": 0.92, "repeat_penalty": 1.18}
    }).encode("utf-8")
    req = urllib.request.Request("http://localhost:11434/api/generate", data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8")).get("response", "").strip()

def humanize_text(txt, model="llama3.2", tone="Natural Everyday"):
    style_guide = TONES.get(tone, TONES["Natural Everyday"])
    prompt = (
        f"You are rewriting AI-generated text so it passes as 100% human-written. Style: {style_guide}\n\n"
        "Rules:\n"
        "- NEVER start with 'In today's fast-paced world' or similar cliches.\n"
        "- NEVER use: crucial, essential, moreover, furthermore, delve, tapestry, testament, robust, seamless, leverage, facilitate, cutting-edge, or revolutionize.\n"
        "- Break long sentences into shorter, simpler ones. Use everyday words a real person would actually type.\n"
        "- Keep the exact same facts and meaning. Output ONLY the rewritten text.\n\n"
        "Example Input:\n"
        "In today's fast-paced world, it is crucial to utilize robust tools to facilitate seamless productivity.\n"
        "Example Output:\n"
        "These days, you really need reliable tools just to keep up and get work done smoothly.\n\n"
        f"Text to rewrite:\n{txt}\n\nRewritten:"
    )
    try:
        res = call_ollama(prompt, model=model, timeout=25)
        if res:
            print(f"Rewritten via Ollama ({model} | {tone}).")
            return offline_humanize(res)
    except Exception as e:
        print(f"Ollama unavailable ({e}), using offline humanizer.")
    return offline_humanize(txt)

def generate_from_prompt(user_prompt, model="llama3.2", tone="Natural Everyday", do_humanize=True):
    style_guide = TONES.get(tone, TONES["Natural Everyday"])
    full_prompt = (
        f"Write a response to the prompt below as a real human would write it. Style: {style_guide}\n\n"
        "Rules:\n"
        "- NEVER use AI cliches or buzzwords like: crucial, essential, moreover, furthermore, delve, tapestry, testament, robust, seamless, leverage, facilitate, cutting-edge, or revolutionize.\n"
        "- Never start with 'In today's fast-paced world' or 'Sure, here is...'.\n"
        "- Vary sentence lengths naturally and use everyday wording.\n"
        "- Output ONLY the requested writing with zero intro, title, or sign-off.\n\n"
        f"Prompt:\n{user_prompt}\n\nResponse:"
    )
    res = call_ollama(full_prompt, model=model, timeout=40)
    if not res:
        return None
    print(f"Generated via Ollama ({model} | {tone}).")
    return offline_humanize(res) if do_humanize else clean_chars(res)
class DeweyMenuBarApp(rumps.App):
    def __init__(self):
        super().__init__("Easy Typer")
        self.is_typing = False
        self.cfg = load_cfg()
        self.hum_item = rumps.MenuItem("AI Humanizer", callback=self.toggle_hum)
        self.hum_item.state = int(self.cfg["humanizer"])

        self.tone_menu = rumps.MenuItem(f"Tone: {self.cfg['tone']}")
        self.tone_items = {}
        for t_name in TONES:
            item = rumps.MenuItem(t_name, callback=self.select_tone)
            item.state = int(t_name == self.cfg["tone"])
            self.tone_items[t_name] = item
            self.tone_menu.add(item)

        self.lbl_spd = rumps.MenuItem(f"Typing Speed: {self.cfg['wpm']} WPM")
        self.lbl_typ = rumps.MenuItem(f"Unfixed Typos: {self.cfg['typo_rate']:.1f}%")
        self.lbl_cor = rumps.MenuItem(f"Self-Corrections: {self.cfg['correction_rate']:.1f}%")
        self.sld_spd = rumps.SliderMenuItem(self.cfg["wpm"], 20, 400, self.on_spd, (190, 22))
        self.sld_typ = rumps.SliderMenuItem(self.cfg["typo_rate"], 0.0, 5.0, self.on_typ, (190, 22))
        self.sld_cor = rumps.SliderMenuItem(self.cfg["correction_rate"], 0.0, 10.0, self.on_cor, (190, 22))

        self.menu = [
            rumps.MenuItem("Type Clipboard", callback=self.start_type_thread),
            rumps.MenuItem("Generate & Type from Prompt", callback=self.start_prompt_thread),
            None,
            self.hum_item,
            self.tone_menu,
            None,
            self.lbl_spd,
            self.sld_spd,
            None,
            self.lbl_typ,
            self.sld_typ,
            None,
            self.lbl_cor,
            self.sld_cor,
            None,
            rumps.MenuItem("Reset Defaults", callback=self.reset_cfg),
            rumps.MenuItem("How to use", callback=self.help_box),
        ]

    def toggle_hum(self, s):
        self.cfg["humanizer"] = not self.cfg["humanizer"]
        s.state = int(self.cfg["humanizer"])
        save_cfg(self.cfg)

    def select_tone(self, sender):
        self.cfg["tone"] = sender.title
        self.tone_menu.title = f"Tone: {sender.title}"
        for name, item in self.tone_items.items():
            item.state = int(name == sender.title)
        save_cfg(self.cfg)

    def on_spd(self, s):
        self.cfg["wpm"] = int(round(s.value / 5.0) * 5)
        self.lbl_spd.title = f"Typing Speed: {self.cfg['wpm']} WPM"
        save_cfg(self.cfg)

    def on_typ(self, s):
        self.cfg["typo_rate"] = round(s.value, 1)
        self.lbl_typ.title = f"Unfixed Typos: {self.cfg['typo_rate']:.1f}%"
        save_cfg(self.cfg)

    def on_cor(self, s):
        self.cfg["correction_rate"] = round(s.value, 1)
        self.lbl_cor.title = f"Self-Corrections: {self.cfg['correction_rate']:.1f}%"
        save_cfg(self.cfg)

    def reset_cfg(self, _):
        self.cfg = DEFAULTS.copy()
        self.sld_spd.value, self.sld_typ.value, self.sld_cor.value = self.cfg["wpm"], self.cfg["typo_rate"], self.cfg["correction_rate"]
        self.hum_item.state = int(self.cfg["humanizer"])
        self.tone_menu.title = f"Tone: {self.cfg['tone']}"
        for name, item in self.tone_items.items():
            item.state = int(name == self.cfg["tone"])
        self.lbl_spd.title, self.lbl_typ.title, self.lbl_cor.title = f"Typing Speed: {self.cfg['wpm']} WPM", f"Unfixed Typos: {self.cfg['typo_rate']:.1f}%", f"Self-Corrections: {self.cfg['correction_rate']:.1f}%"
        save_cfg(self.cfg)

    def help_box(self, _):
        rumps.alert("How to Use Dewey AI", "1. Copy text OR a writing prompt (Cmd+C).\n2. Pick your Tone and sliders.\n3. Click 'Type Clipboard' (to humanize & type copied text) OR 'Generate & Type from Prompt' (to have Ollama write from your prompt).\n4. Click inside your document during the 5s countdown.\n\nForce Quit: Move mouse to any screen corner.")

    def read_clipboard(self):
        try:
            txt = subprocess.check_output("pbpaste", shell=True).decode("utf-8")
        except Exception as e:
            rumps.alert("Error", str(e))
            return None
        if not txt.strip():
            rumps.alert("Clipboard Empty", "Copy some text or a prompt first!")
            return None
        return txt

    def start_type_thread(self, _):
        if self.is_typing: return
        txt = self.read_clipboard()
        if txt:
            self.is_typing = True
            threading.Thread(target=self.type_worker, args=(txt, "humanize"), daemon=True).start()

    def start_prompt_thread(self, _):
        if self.is_typing: return
        txt = self.read_clipboard()
        if txt:
            self.is_typing = True
            threading.Thread(target=self.type_worker, args=(txt, "prompt"), daemon=True).start()

    def type_worker(self, raw, mode="humanize"):
        try:
            model = self.cfg.get("model", "llama3.2")
            tone = self.cfg.get("tone", "Natural Everyday")
            if mode == "prompt":
                self.title = "Generating..."
                try:
                    txt = generate_from_prompt(raw, model, tone, self.cfg["humanizer"])
                except Exception as e:
                    print(f"Ollama prompt failed: {e}")
                    txt = None
                if not txt:
                    rumps.alert("Ollama Error", "Could not generate text. Make sure Ollama is open and running!")
                    return
            else:
                self.title = "Rewriting..."
                txt = humanize_text(raw, model, tone) if self.cfg["humanizer"] else clean_chars(raw)

            for s in range(5, 0, -1):
                self.title = f"Typing in {s}s"
                print(f"{s}...")
                time.sleep(1)
            self.title = "Typing..."
            keys = {"a": "qwsz", "b": "vghn", "c": "xvdf", "d": "ersfxc", "e": "wsdr", "f": "rtgvcd", "g": "tyhbvf", "h": "yujnbg", "i": "ujko", "j": "uikmnh", "k": "ijlm", "l": "okp", "m": "njk", "n": "bhjm", "o": "iklp", "p": "ol", "q": "wa", "r": "edft", "s": "wedxza", "t": "rfgy", "u": "yhji", "v": "cfgb", "w": "qase", "x": "zsdc", "y": "tghu", "z": "asx"}
            cnt, nxt, buf = 0, random.randint(25, 45), ""
            for ch in txt:
                if ch == "\r": continue
                wpm = max(self.cfg["wpm"], 1)
                base, sc = 60.0 / (wpm * 5.0), min(1.0, 95.0 / wpm)
                if ch == "\n":
                    if buf: pyautogui.write(buf); buf = ""
                    pyautogui.press("enter")
                    time.sleep(random.uniform(base * 2.0, base * 4.0))
                    continue
                d = random.uniform(base * 1.4, base * 2.8) if ch in "., " else random.uniform(base * 0.65, base * 1.35)
                cnt += 1
                if cnt >= nxt:
                    if buf: pyautogui.write(buf); buf = ""
                    time.sleep(random.uniform(0.25, 0.5) * sc)
                    cnt, nxt = 0, random.randint(25, 45)
                r, u_p, c_p = random.random(), self.cfg["typo_rate"] / 100.0, self.cfg["correction_rate"] / 100.0
                if ch.lower() in keys and r < (u_p + c_p):
                    if buf: pyautogui.write(buf); buf = ""
                    w = random.choice(keys[ch.lower()])
                    w = w.upper() if ch.isupper() else w
                    if r < u_p:
                        pyautogui.write(w)
                        time.sleep(d)
                        continue
                    pyautogui.write(w)
                    time.sleep(random.uniform(0.12, 0.22) * sc)
                    pyautogui.press("backspace")
                    time.sleep(random.uniform(0.06, 0.12) * sc)
                if wpm > 160 and ch not in " \n.,!?":
                    buf += ch
                else:
                    if buf:
                        pyautogui.write(buf + ch)
                        time.sleep(d * (len(buf) + 1))
                        buf = ""
                    else:
                        pyautogui.write(ch)
                        time.sleep(d)
            if buf: pyautogui.write(buf)
            print("Done.")
        except pyautogui.FailSafeException:
            print("Stopped via failsafe.")
        finally:
            self.title = "Easy Typer"
            self.is_typing = False

if __name__ == "__main__":
    DeweyMenuBarApp().run()
