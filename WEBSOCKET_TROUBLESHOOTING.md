# WebSocket 连接故障排除指南

## 🔍 问题诊断

如果您遇到 WebSocket 连接失败的问题，请按照以下步骤进行诊断和修复。

## 📋 快速检查清单

### 1. 服务状态检查

确保以下服务正在运行：

```bash
# 检查后端服务 (端口 8000)
netstat -an | grep :8000

# 检查前端服务 (端口 3000)  
netstat -an | grep :3000
```

### 2. 健康检查

测试后端API是否正常：

```bash
curl http://localhost:8000/api/health
```

预期响应：
```json
{"status":"healthy","timestamp":"2025-06-23T13:47:01.123456"}
```

### 3. WebSocket 连接测试

使用提供的测试工具：

```bash
# Python 测试脚本
python test_websocket.py

# 诊断工具
python websocket_diagnosis.py
```

## 🛠️ 常见问题及解决方案

### 问题 1: 后端服务未启动

**症状**: 无法连接到 `ws://localhost:8000/ws`

**解决方案**:
```bash
# 进入后端目录
cd backend

# 启动后端服务
python start_simple_server.py
```

### 问题 2: 前端服务未启动

**症状**: 前端页面无法访问或WebSocket连接失败

**解决方案**:
```bash
# 进入前端目录
cd frontend

# 安装依赖（如果需要）
npm install

# 启动前端服务
npm start
```

### 问题 3: 端口被占用

**症状**: 服务启动失败，提示端口被占用

**解决方案**:
```bash
# 查看端口占用情况
netstat -ano | findstr :8000

# 终止占用端口的进程
taskkill /PID <进程ID> /F
```

### 问题 4: 防火墙阻止连接

**症状**: 本地连接正常，但外部无法访问

**解决方案**:
1. 检查 Windows 防火墙设置
2. 添加端口 8000 和 3000 到防火墙例外
3. 或临时关闭防火墙进行测试

### 问题 5: CORS 错误

**症状**: 浏览器控制台显示 CORS 错误

**解决方案**:
检查后端 CORS 配置是否正确：

```python
# 在 backend/simple_main.py 中确认
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 问题 6: 依赖包缺失

**症状**: 启动服务时出现 ImportError

**解决方案**:
```bash
# 安装后端依赖
cd backend
pip install -r requirements.txt

# 安装前端依赖
cd frontend
npm install
```

## 🔧 调试工具

### 1. WebSocket 调试页面

打开 `websocket_debug.html` 进行详细的 WebSocket 连接测试：

```bash
# 在浏览器中打开
file:///path/to/websocket_debug.html
```

### 2. 浏览器开发者工具

1. 打开浏览器开发者工具 (F12)
2. 查看 Console 面板的错误信息
3. 查看 Network 面板的 WebSocket 连接状态

### 3. 后端日志

查看后端服务日志：

```bash
# 查看实时日志
tail -f backend/china_server.log
```

## 📱 前端 WebSocket 使用

### 连接 WebSocket

```javascript
import { wsService } from '../services/api';

// 连接 WebSocket
await wsService.connect();

// 监听消息
wsService.on('message', (data) => {
    console.log('收到消息:', data);
});

// 监听连接状态
wsService.on('connection', (data) => {
    console.log('连接已建立:', data.message);
});
```

### 发送消息

```javascript
// 发送测试消息
wsService.send({
    type: 'test',
    message: 'Hello from client',
    timestamp: new Date().toISOString()
});
```

## 🚀 一键启动系统

使用提供的启动脚本：

```bash
# 启动整个系统（前端 + 后端）
python start_system.py
```

## 📞 获取帮助

如果问题仍然存在，请：

1. 运行诊断工具：`python websocket_diagnosis.py`
2. 查看浏览器控制台错误信息
3. 检查后端服务日志
4. 确认所有依赖已正确安装

## ✅ 验证连接成功

当 WebSocket 连接成功时，您应该看到：

1. 前端页面显示 "WebSocket 连接已建立"
2. 浏览器控制台没有 WebSocket 相关错误
3. 后端日志显示新的 WebSocket 连接
4. 可以正常发送和接收消息

## 🔄 自动重连

系统已配置自动重连机制：

- 最大重连次数：5 次
- 重连间隔：递增延迟（1秒、2秒、4秒...）
- 连接断开时自动尝试重连

## 📊 监控连接状态

使用提供的调试工具监控：

- 连接次数
- 消息数量  
- 错误次数
- 重连次数

---

**注意**: 本指南适用于开发环境。生产环境请相应调整安全配置。 