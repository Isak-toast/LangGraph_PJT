# Page snapshot

```yaml
- generic [ref=e3]:
  - generic [ref=e4]: "[plugin:vite:css] [postcss] tailwindcss: /home/isak/LangGraph_PJT/langgraph_web_ui/client/src/style.css:1:1: Cannot apply unknown utility class `border-border`. Are you using CSS modules or similar and missing `@reference`? https://tailwindcss.com/docs/functions-and-directives#reference-directive"
  - generic [ref=e5]: /home/isak/LangGraph_PJT/langgraph_web_ui/client/src/style.css:1:0
  - generic [ref=e6]: 1 | @tailwind base; | ^ 2 | @tailwind components; 3 | @tailwind utilities;
  - generic [ref=e7]: at Input.error (/home/isak/LangGraph_PJT/langgraph_web_ui/client/node_modules/postcss/lib/input.js:135:16) at Root.error (/home/isak/LangGraph_PJT/langgraph_web_ui/client/node_modules/postcss/lib/node.js:146:32) at Object.Once (/home/isak/LangGraph_PJT/langgraph_web_ui/client/node_modules/@tailwindcss/postcss/dist/index.js:10:6911) at async LazyResult.runAsync (/home/isak/LangGraph_PJT/langgraph_web_ui/client/node_modules/postcss/lib/lazy-result.js:293:11) at async runPostCSS (file:///home/isak/LangGraph_PJT/langgraph_web_ui/client/node_modules/vite/dist/node/chunks/config.js:30144:19) at async compilePostCSS (file:///home/isak/LangGraph_PJT/langgraph_web_ui/client/node_modules/vite/dist/node/chunks/config.js:30128:6) at async compileCSS (file:///home/isak/LangGraph_PJT/langgraph_web_ui/client/node_modules/vite/dist/node/chunks/config.js:30058:26) at async TransformPluginContext.handler (file:///home/isak/LangGraph_PJT/langgraph_web_ui/client/node_modules/vite/dist/node/chunks/config.js:29591:54) at async EnvironmentPluginContainer.transform (file:///home/isak/LangGraph_PJT/langgraph_web_ui/client/node_modules/vite/dist/node/chunks/config.js:28796:14) at async loadAndTransform (file:///home/isak/LangGraph_PJT/langgraph_web_ui/client/node_modules/vite/dist/node/chunks/config.js:22669:26)
  - generic [ref=e8]:
    - text: Click outside, press Esc key, or fix the code to dismiss.
    - text: You can also disable this overlay by setting
    - code [ref=e9]: server.hmr.overlay
    - text: to
    - code [ref=e10]: "false"
    - text: in
    - code [ref=e11]: vite.config.ts
    - text: .
```