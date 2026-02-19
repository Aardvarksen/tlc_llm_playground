# Creating the Moodle Content Extraction Bookmarklet

This guide shows you how to create a browser bookmarklet that extracts page content from Moodle, exactly the way Moodle's built-in AI features do.

## Why Use a Bookmarklet?

The TLC LLM Playground needs page content to test how different models respond to Moodle's AI functions (Summarise, Explain, Generate). Rather than manually copying text, this bookmarklet:

1. **Extracts the exact same content** that Moodle's AI would see
2. **Copies it to your clipboard** with one click
3. **Works on any Moodle page** where you're logged in

## Why This Is the Best Approximation to Moodle Integration

Moodle's AI placement system uses JavaScript to extract content from the page before sending it to an LLM. Specifically, it grabs all text from the `[role="main"]` element:

```javascript
// From Moodle source: ai/placement/courseassist/amd/src/placement.js
getTextContent() {
    const mainRegion = document.querySelector('[role="main"]');
    return mainRegion.innerText || mainRegion.textContent;
}
```

Our bookmarklet does **exactly the same thing** - it finds `[role="main"]` and extracts its text. This means:

- The content you paste into the Playground is identical to what Moodle's AI would receive
- You can test whether a model produces useful output with real Moodle page content
- Results in the Playground predict how the model would behave when integrated with Moodle

## Creating the Bookmarklet

### Chrome / Firefox

1. Right-click your browser's bookmarks bar
2. Select "Add page..." or "Add bookmark..."
3. Give it a name: `Moodle Extract Main`
4. In the URL/Location field, paste the bookmarklet code below
5. Click "Save" or "Done"

### Microsoft Edge

Edge doesn't let you enter a custom URL when adding a favorite from the right-click menu. You need to get to the **Favorites page** (`edge://favorites`) first. Either way works:

- **Option A**: Right-click the favorites bar → **Manage favorites**
- **Option B**: `Ctrl+Shift+O` to open the favorites menu → click the **three-dots** icon (⋯) → **Open favorites page**

Once you're on the Favorites page:

1. Click **Add favorite** in the toolbar
2. A popup will appear — give it a name: `Moodle Extract Main`
3. In the URL field, paste the bookmarklet code below
4. Click "Save"

### The Bookmarklet Code

Paste this entire line into the URL field when creating your bookmark:

```
javascript:(function(){const m=document.querySelector('[role="main"]');if(!m){alert('No [role="main"] found');return;}const t=m.innerText;navigator.clipboard.writeText(t).then(()=>alert('Copied '+t.length+' chars to clipboard'));})();
```

You should now see "Moodle Extract Main" in your bookmarks/favorites bar.

## Using the Bookmarklet

### Prerequisites

- **You must be logged into Moodle** - The bookmarklet runs on pages you can see
- **You must be viewing the page you want to extract** - Navigate to the course, activity, or resource first

### Steps

1. Navigate to any Moodle page (course page, quiz, lesson, resource, etc.)
2. Click the "Moodle Extract Main" bookmarklet in your bookmarks bar
3. You'll see an alert: "Copied X chars to clipboard"
4. Go to the TLC LLM Playground's Side-by-Side page
5. Paste (Ctrl+V / Cmd+V) into the "Content" text area
6. Select a Moodle function and models, then click Generate

## What Gets Captured

The `[role="main"]` region contains:

- **Course/Activity header** - Title, breadcrumbs, completion info
- **Main content** - The actual page content (varies by activity type)
- **Navigation elements** - Previous/Next buttons, activity navigation
- **UI text** - Button labels, status messages

This is intentional - it's exactly what Moodle's AI features see. If the model can produce a useful summary despite the "noise" of navigation text, it will work when integrated with Moodle.

## Known Limitations

### Iframe Content Is Not Captured

The bookmarklet (and Moodle's AI) cannot extract content from `<iframe>` elements. This affects:

- **URL resources** embedding external content (e.g., Pressbooks chapters)
- **H5P interactive content**
- **SCORM packages**
- **LTI external tools**
- **Some embedded media players**

For these content types, you'll see only the fallback text (like "Click to open resource") rather than the actual educational content.

**This is a fundamental limitation of Moodle's AI integration** - the TLC LLM Playground accurately replicates this behavior so you can identify which content types work well with AI features and which don't.

## Troubleshooting

### "No [role="main"] found"

- You may be on a page that doesn't use Moodle's standard template
- Try navigating to a different page (course home, specific activity)
- Check that you're actually on a Moodle site

### Clipboard Permission Denied

Some browsers require explicit permission for clipboard access:

1. Click the lock/info icon in the address bar
2. Find "Clipboard" in the permissions
3. Set to "Allow"

### Very Short Content Copied

If only a few characters were copied:
- The page may be loading content dynamically - wait for it to fully load
- The main content might be in an iframe (see limitations above)
- Check that you're viewing the content page, not just an index

## Technical Details

The bookmarklet code, formatted for readability:

```javascript
(function() {
    // Find the main content region (same selector Moodle uses)
    const m = document.querySelector('[role="main"]');

    // Check if element exists
    if (!m) {
        alert('No [role="main"] found');
        return;
    }

    // Extract visible text content
    const t = m.innerText;

    // Copy to clipboard and show confirmation
    navigator.clipboard.writeText(t).then(() =>
        alert('Copied ' + t.length + ' chars to clipboard')
    );
})();
```

This matches Moodle's implementation in `ai/placement/courseassist/amd/src/placement.js` (line 527-530).
