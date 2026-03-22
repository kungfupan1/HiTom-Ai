// 全局注册常用图标
import {
  User,
  Lock,
  Plus,
  Close,
  Delete,
  Check,
  Document,
  Loading,
  Coin,
  ArrowDown,
  Expand,
  Fold,
  ZoomIn,
  Download,
  ArrowLeft,
  ArrowRight,
  Shop,
  Cpu,
  MagicStick
} from '@element-plus/icons-vue'

// 常用图标映射
export const icons = {
  User,
  Lock,
  Plus,
  Close,
  Delete,
  Check,
  Document,
  Loading,
  Coin,
  ArrowDown,
  Expand,
  Fold,
  ZoomIn,
  Download,
  ArrowLeft,
  ArrowRight,
  Shop,
  Cpu,
  MagicStick
}

// 注册到全局
export function registerIcons(app) {
  Object.entries(icons).forEach(([name, component]) => {
    app.component(name, component)
  })
}

export default icons