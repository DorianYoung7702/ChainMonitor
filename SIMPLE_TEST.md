# ChainMonitor 简化测试指南（无需数据库）

如果您的环境中没有Docker或PostgreSQL，可以使用这个简化方案快速测试前端功能。

## 🚀 前端独立测试（3分钟）

前端已经内置了mock数据，可以完全独立运行，无需后端和数据库。

### 步骤1: 安装前端依赖

```bash
cd frontend
npm install
```

### 步骤2: 配置环境变量（可选）

```bash
# 创建.env文件
cp .env.example .env
```

即使不填写真实的配置，前端也能正常运行（使用mock数据）。

### 步骤3: 启动开发服务器

```bash
npm run dev
```

### 步骤4: 访问前端

打开浏览器访问: **http://localhost:3000**

## ✅ 前端功能测试清单

### Dashboard页面
- [x] 显示全局风险状态（Level 2 - WARNING）
- [x] 显示综合评分（62/100）
- [x] 三个关键指标卡片：
  - DEX活跃度: 28/40
  - 巨鲸抛压: 21/35
  - CEX流动: 13/30
- [x] 风险趋势图表（24小时）
- [x] 因子柱状图
- [x] 监控市场卡片
- [x] 最新事件流

### Market Detail页面
- [x] 点击市场卡片进入详情
- [x] 当前风险等级展示
- [x] 三个因子详细卡片
- [x] 风险历史图表
- [x] 最近交易表格
- [x] Etherscan链接

### Alerts页面
- [x] 告警配置界面
- [x] 风险阈值滑块
- [x] 市场选择下拉菜单
- [x] 告警历史记录
- [x] 保存配置按钮

### 交互测试
- [x] 页面切换动画
- [x] 卡片悬停效果
- [x] 响应式布局
- [x] 图表交互

## 📊 Mock数据说明

前端使用的mock数据位于：
- `frontend/src/hooks/useRiskData.ts` - 市场风险数据
- `frontend/src/hooks/useAlerts.ts` - 告警数据

数据特点：
- 市场: UNISWAP_USDC_WETH
- 风险等级: Level 2 (警告)
- 综合评分: 62/100
- 包含完整的因子数据和历史趋势

## 🔧 如果前端也遇到问题

### 问题1: 端口被占用

```bash
# 修改端口
npm run dev -- --port 3001
```

### 问题2: 依赖安装失败

```bash
# 清理缓存
rm -rf node_modules package-lock.json
npm install

# 或使用yarn
npm install -g yarn
yarn install
```

### 问题3: 构建错误

```bash
# 检查Node版本（需要18+）
node --version

# 更新到Node 18+
# 然后重新安装依赖
npm install
```

---

## 💻 完整测试（需要数据库）

如果您有Docker或PostgreSQL，请参考 [TESTING_GUIDE.md](TESTING_GUIDE.md)

### 使用Docker（推荐）

```bash
# 启动PostgreSQL
docker-compose up -d postgres

# 设置数据库
cd database
./setup-docker.sh

# 测试API
python3 examples/api_integration.py
```

### 使用本地PostgreSQL

```bash
cd database
./setup.sh
```

---

## 🎯 测试重点

由于前端已经包含完整的UI和交互逻辑，您可以专注测试：

1. **视觉设计** - Dune风格的深色主题
2. **数据可视化** - 图表和指标展示
3. **交互体验** - 页面切换、悬停效果
4. **响应式设计** - 不同屏幕尺寸的适配
5. **组件功能** - 所有UI组件的正常工作

---

## 📝 下一步

测试完前端后，您可以：

1. **集成真实数据**
   - 设置PostgreSQL数据库
   - 运行测试数据生成器
   - 修改前端hooks连接API

2. **部署智能合约**
   - 编译和部署到Sepolia
   - 获取合约地址
   - 测试钱包连接

3. **运行后端监控**
   - 获取Infura RPC密钥
   - 配置环境变量
   - 启动监控脚本

---

**快速开始前端测试**:

```bash
cd frontend && npm install && npm run dev
```

然后访问 http://localhost:3000
