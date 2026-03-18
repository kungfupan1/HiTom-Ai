<template>
  <router-view />
</template>

<script setup>
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
  background-color: #0a0a0f;
  color: #fff;
}

/* 赛博朋克风格全局样式 */
.cyber-glass {
  background: rgba(0, 0, 0, 0.4) !important;
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: 12px;
}

.gradient-text {
  background: linear-gradient(90deg, #00f260, #0575e6);
  -webkit-background-clip: text;
  color: transparent;
  font-weight: bold;
}

.neon-btn {
  background: linear-gradient(90deg, #7f00ff, #e100ff) !important;
  border: none;
  box-shadow: 0 4px 15px rgba(127, 0, 255, 0.4);
}

.neon-btn:hover {
  opacity: 0.9;
}
</style>