# MCP Prompt Optimizer - Troubleshooting Guide / 故障排除指南

[![English](https://img.shields.io/badge/Language-English-blue.svg)](#english) [![中文](https://img.shields.io/badge/语言-中文-red.svg)](#中文)

---

## English

### 🔧 **Comprehensive Troubleshooting Guide**

This guide covers solutions for common issues with the MCP Prompt Optimizer system. Issues are organized by category with step-by-step solutions.

---

## 📋 **Quick Diagnostic Checklist**

Before diving into specific issues, run this quick diagnostic:

```bash
# 1. Check Python version
python3 --version
# Expected: Python 3.8.0 or higher

# 2. Check if in virtual environment
echo $VIRTUAL_ENV
# Expected: Shows path to venv directory

# 3. Test MCP server directly
python3 prompt_optimizer.py
# Expected: Server starts without errors

# 4. Check Claude Desktop config
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
# Expected: Contains "prompt-optimizer" entry
```

**✅ All checks pass?** → Your system is healthy!  
**❌ Any check fails?** → Continue to specific issue sections below.

---

## 🚫 **Installation Issues**

### **Issue 1: Python Version Too Old**

**❌ Error:**
```
Python 3.7.x is not supported. Requires Python 3.8+
```

**✅ Solution:**
```bash
# macOS (using Homebrew)
brew install python@3.11
brew link python@3.11

# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv

# Windows
# Download from https://python.org/downloads/
```

### **Issue 2: Virtual Environment Creation Failed**

**❌ Error:**
```
Error: Unable to create virtual environment
```

**✅ Solution:**
```bash
# Method 1: Manual creation
python3 -m venv venv --clear
source venv/bin/activate  # Windows: venv\Scripts\activate

# Method 2: Alternative venv tool
pip install virtualenv
virtualenv venv
source venv/bin/activate

# Method 3: Force recreation
rm -rf venv
python3 -m venv venv
source venv/bin/activate
```

### **Issue 3: Dependencies Installation Failed**

**❌ Error:**
```
ERROR: Could not install packages due to an EnvironmentError
```

**✅ Solution:**
```bash
# Method 1: Upgrade pip first
python3 -m pip install --upgrade pip

# Method 2: Install with verbose output
pip install -r requirements.txt -v

# Method 3: Install individually
pip install mcp
pip install dspy-ai
pip install sentence-transformers
pip install scikit-learn
pip install redis

# Method 4: Use conda (if available)
conda install -c conda-forge mcp
```

---

## 🔌 **MCP Connection Issues**

### **Issue 4: Claude Desktop Not Recognizing MCP Server**

**❌ Symptoms:**
- Commands not recognized in Claude Desktop
- "Tool not found" errors
- MCP server appears offline

**✅ Diagnostic Steps:**
```bash
# 1. Check config file location
# macOS
ls ~/Library/Application\ Support/Claude/
# Windows
ls $APPDATA/Claude/
# Linux
ls ~/.config/Claude/

# 2. Verify config content
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# 3. Test server manually
cd /path/to/mcp-prompt-optimizer
python3 prompt_optimizer.py
```

**✅ Solutions:**

**Step 1: Verify Configuration**
```json
{
  "mcpServers": {
    "prompt-optimizer": {
      "command": "python3",
      "args": ["/absolute/path/to/prompt_optimizer.py"],
      "env": {}
    }
  }
}
```

**Step 2: Fix Common Config Issues**
```bash
# Fix 1: Use absolute paths
pwd  # Get current directory
# Update config with full path: /Users/username/mcp-prompt-optimizer/prompt_optimizer.py

# Fix 2: Check file permissions
chmod +x prompt_optimizer.py

# Fix 3: Verify Python executable
which python3
# Update config with full Python path if needed
```

**Step 3: Restart Claude Desktop**
```bash
# macOS
osascript -e 'quit app "Claude"'
open /Applications/Claude.app

# Windows
taskkill /f /im Claude.exe
# Restart from Start Menu

# Linux
killall claude
claude &
```

### **Issue 5: MCP Server Starts But Tools Not Available**

**❌ Error:**
```
MCP server running but tools not listed
```

**✅ Solution:**
```bash
# 1. Check server logs
python3 prompt_optimizer.py 2>&1 | tee server.log

# 2. Enable debug mode
export MCP_LOG_LEVEL=debug
python3 prompt_optimizer.py

# 3. Verify tool registration
grep -i "tool" server.log

# 4. Test tool listing
# In Claude Desktop: "List available tools"
```

---

## ⚡ **Performance Issues**

### **Issue 6: Slow Optimization Performance**

**❌ Symptoms:**
- Optimization takes >30 seconds
- Frequent timeouts
- Poor response times

**✅ Diagnostic:**
```bash
# Check system resources
top | grep python

# Monitor optimization performance
python3 -c "
from prompt_optimizer import *
import time
start = time.time()
# Run test optimization
print(f'Time taken: {time.time() - start:.2f}s')
"
```

**✅ Solutions:**

**Step 1: Optimize Environment**
```bash
# Close unnecessary applications
# Ensure sufficient RAM (2GB+ available)
# Check disk space: df -h

# Restart system if needed
```

**Step 2: Configure Performance Settings**
```python
# In prompt_optimizer.py, adjust these settings:
CACHE_SIZE = 1000  # Reduce if low memory
MAX_WORKERS = 2    # Reduce concurrent processing
TIMEOUT = 30       # Increase timeout if needed
```

**Step 3: Database Optimization**
```bash
# Check database file size
ls -lh optimization_data.db

# Vacuum database if large
python3 -c "
import sqlite3
conn = sqlite3.connect('optimization_data.db')
conn.execute('VACUUM')
conn.close()
"
```

### **Issue 7: Memory Usage Too High**

**❌ Symptoms:**
- System becomes slow during optimization
- Out of memory errors
- High RAM usage

**✅ Solution:**
```python
# Optimize memory usage in prompt_optimizer.py
import gc

# Add garbage collection
def optimize_memory():
    gc.collect()
    
# Limit embedding cache size
EMBEDDING_CACHE_SIZE = 100  # Reduce from default

# Use batch processing for large operations
BATCH_SIZE = 10  # Process in smaller batches
```

---

## 🎯 **DSPy Optimization Issues**

### **Issue 8: Poor Optimization Results**

**❌ Symptoms:**
- Low improvement percentages (<10%)
- Optimization results seem irrelevant
- Strategy selection appears incorrect

**✅ Diagnostic:**
```bash
# Check example mining quality
python3 -c "
from dspy_example_miner import DSPyExampleMiner
miner = DSPyExampleMiner()
examples = miner.mine_examples('test_task')
print(f'Found {len(examples)} examples')
for ex in examples[:3]:
    print(f'Quality: {ex.quality_score:.2f}')
"
```

**✅ Solutions:**

**Step 1: Improve Input Quality**
```plaintext
# Instead of vague prompts:
"help me"

# Provide specific, contextual prompts:
"As a Python developer, help me optimize this API endpoint for better performance"
```

**Step 2: Use Optimization Targets**
```plaintext
# For detailed analysis:
dspy_optimize with optimize_for=quality

# For quick tasks:
dspy_optimize with optimize_for=speed

# For creative work:
dspy_optimize with optimize_for=creativity
```

**Step 3: Provide Feedback**
```plaintext
# After each optimization:
provide_strategy_feedback with:
- session_id: [from optimization result]
- feedback_score: 1-5
- comments: "More specific guidance needed"
```

### **Issue 9: DSPy Module Compilation Failures**

**❌ Error:**
```
DSPy compilation failed: Module optimization timeout
```

**✅ Solution:**
```python
# Check DSPy configuration
import dspy

# Verify LM configuration
print(dspy.settings.lm)

# Test basic DSPy functionality
class SimpleSignature(dspy.Signature):
    input = dspy.InputField()
    output = dspy.OutputField()

# Test compilation
try:
    module = dspy.ChainOfThought(SimpleSignature)
    result = module(input="test")
    print("DSPy working correctly")
except Exception as e:
    print(f"DSPy issue: {e}")
```

---

## 💾 **Database Issues**

### **Issue 10: Database Corruption**

**❌ Error:**
```
sqlite3.DatabaseError: database disk image is malformed
```

**✅ Solution:**
```bash
# Backup current database
cp optimization_data.db optimization_data.db.backup

# Try to repair
python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('optimization_data.db')
    conn.execute('PRAGMA integrity_check')
    conn.execute('VACUUM')
    conn.close()
    print('Database repaired successfully')
except Exception as e:
    print(f'Repair failed: {e}')
"

# If repair fails, reinitialize
rm optimization_data.db
python3 setup_qa_database.py
```

### **Issue 11: Database Permission Issues**

**❌ Error:**
```
PermissionError: [Errno 13] Permission denied: 'optimization_data.db'
```

**✅ Solution:**
```bash
# Check file permissions
ls -la optimization_data.db

# Fix permissions
chmod 644 optimization_data.db
chown $USER:$USER optimization_data.db

# If in Docker/container
chown 1000:1000 optimization_data.db
```

---

## 🌐 **Network and External Dependencies**

### **Issue 12: Redis Connection Failed**

**❌ Error:**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**✅ Solution:**
```bash
# Option 1: Install Redis locally
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis

# Windows
# Download from https://redis.io/download

# Option 2: Use in-memory fallback
# System automatically falls back to memory caching if Redis unavailable
# No action needed - this is expected behavior
```

### **Issue 13: Model Download Issues**

**❌ Error:**
```
OSError: Can't load tokenizer for 'sentence-transformers/all-MiniLM-L6-v2'
```

**✅ Solution:**
```bash
# Pre-download models
python3 -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
print('Model downloaded successfully')
"

# If download fails, use proxy or alternative mirror
export HF_ENDPOINT=https://hf-mirror.com
python3 -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
"
```

---

## 🔍 **Advanced Debugging**

### **Debug Mode Activation**
```bash
# Enable comprehensive logging
export MCP_LOG_LEVEL=debug
export PYTHONPATH=$PWD:$PYTHONPATH

# Run with detailed output
python3 prompt_optimizer.py 2>&1 | tee debug.log

# Analyze logs
grep -i "error\|warning\|exception" debug.log
```

### **Performance Profiling**
```python
# Add to prompt_optimizer.py for profiling
import cProfile
import pstats

def profile_optimization(prompt):
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run optimization
    result = dspy_optimizer.one_click_optimize(prompt)
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)
    
    return result
```

### **Memory Profiling**
```bash
# Install memory profiler
pip install memory-profiler

# Profile memory usage
python3 -m memory_profiler prompt_optimizer.py
```

---

## 📞 **Getting Help**

### **Before Reporting Issues**
1. ✅ **Check this troubleshooting guide**
2. ✅ **Run diagnostic checklist**
3. ✅ **Search existing GitHub issues**
4. ✅ **Test with minimal example**

### **How to Report Issues**
When reporting issues, please include:

```bash
# System information
python3 --version
pip list | grep -E "(mcp|dspy|sentence)"
uname -a

# Error logs
tail -n 50 debug.log

# Configuration
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Test case
echo "Minimal prompt that reproduces the issue"
```

### **Support Channels**
- 🐛 **GitHub Issues**: Technical bugs and feature requests
- 📚 **Documentation**: [User Guide](user-guide.md) for detailed usage
- ⚡ **Quick Help**: [Quick Start](quick-start.md) for basic setup

---

## 中文

### 🔧 **全面故障排除指南**

本指南涵盖了MCP Prompt Optimizer系统常见问题的解决方案。问题按类别组织，提供逐步解决方案。

---

## 📋 **快速诊断检查表**

在深入特定问题之前，运行此快速诊断：

```bash
# 1. 检查Python版本
python3 --version
# 预期：Python 3.8.0或更高版本

# 2. 检查是否在虚拟环境中
echo $VIRTUAL_ENV
# 预期：显示venv目录路径

# 3. 直接测试MCP服务器
python3 prompt_optimizer.py
# 预期：服务器无错误启动

# 4. 检查Claude Desktop配置
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
# 预期：包含"prompt-optimizer"条目
```

**✅ 所有检查都通过？** → 您的系统是健康的！  
**❌ 任何检查失败？** → 继续到下面的特定问题部分。

---

## 🚫 **安装问题**

### **问题1：Python版本过旧**

**❌ 错误：**
```
Python 3.7.x不被支持。需要Python 3.8+
```

**✅ 解决方案：**
```bash
# macOS（使用Homebrew）
brew install python@3.11
brew link python@3.11

# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv

# Windows
# 从https://python.org/downloads/下载
```

### **问题2：虚拟环境创建失败**

**❌ 错误：**
```
错误：无法创建虚拟环境
```

**✅ 解决方案：**
```bash
# 方法1：手动创建
python3 -m venv venv --clear
source venv/bin/activate  # Windows: venv\Scripts\activate

# 方法2：使用替代venv工具
pip install virtualenv
virtualenv venv
source venv/bin/activate

# 方法3：强制重新创建
rm -rf venv
python3 -m venv venv
source venv/bin/activate
```

---

## 🔌 **MCP连接问题**

### **问题4：Claude Desktop无法识别MCP服务器**

**❌ 症状：**
- Claude Desktop中命令无法识别
- "工具未找到"错误
- MCP服务器显示离线

**✅ 诊断步骤：**
```bash
# 1. 检查配置文件位置
# macOS
ls ~/Library/Application\ Support/Claude/
# Windows
ls $APPDATA/Claude/
# Linux
ls ~/.config/Claude/

# 2. 验证配置内容
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# 3. 手动测试服务器
cd /path/to/mcp-prompt-optimizer
python3 prompt_optimizer.py
```

**✅ 解决方案：**

**步骤1：验证配置**
```json
{
  "mcpServers": {
    "prompt-optimizer": {
      "command": "python3",
      "args": ["/absolute/path/to/prompt_optimizer.py"],
      "env": {}
    }
  }
}
```

**步骤2：修复常见配置问题**
```bash
# 修复1：使用绝对路径
pwd  # 获取当前目录
# 使用完整路径更新配置：/Users/username/mcp-prompt-optimizer/prompt_optimizer.py

# 修复2：检查文件权限
chmod +x prompt_optimizer.py

# 修复3：验证Python可执行文件
which python3
# 如需要，使用完整Python路径更新配置
```

---

## ⚡ **性能问题**

### **问题6：优化性能缓慢**

**❌ 症状：**
- 优化耗时>30秒
- 频繁超时
- 响应时间差

**✅ 解决方案：**

**步骤1：优化环境**
```bash
# 关闭不必要的应用程序
# 确保足够的RAM（2GB+可用）
# 检查磁盘空间：df -h

# 如需要重启系统
```

**步骤2：配置性能设置**
```python
# 在prompt_optimizer.py中调整这些设置：
CACHE_SIZE = 1000  # 如果内存不足则减少
MAX_WORKERS = 2    # 减少并发处理
TIMEOUT = 30       # 如需要增加超时时间
```

---

## 🎯 **DSPy优化问题**

### **问题8：优化结果差**

**❌ 症状：**
- 低改进百分比（<10%）
- 优化结果似乎不相关
- 策略选择似乎不正确

**✅ 解决方案：**

**步骤1：改进输入质量**
```plaintext
# 而不是模糊提示：
"帮助我"

# 提供具体的、有上下文的提示：
"作为Python开发者，帮我优化这个API端点以获得更好的性能"
```

**步骤2：使用优化目标**
```plaintext
# 用于详细分析：
dspy_optimize，目标为质量

# 用于快速任务：
dspy_optimize，目标为速度

# 用于创意工作：
dspy_optimize，目标为创意
```

**步骤3：提供反馈**
```plaintext
# 每次优化后：
provide_strategy_feedback：
- session_id：[来自优化结果]
- feedback_score：1-5
- comments："需要更具体的指导"
```

---

## 💾 **数据库问题**

### **问题10：数据库损坏**

**❌ 错误：**
```
sqlite3.DatabaseError: database disk image is malformed
```

**✅ 解决方案：**
```bash
# 备份当前数据库
cp optimization_data.db optimization_data.db.backup

# 尝试修复
python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('optimization_data.db')
    conn.execute('PRAGMA integrity_check')
    conn.execute('VACUUM')
    conn.close()
    print('数据库修复成功')
except Exception as e:
    print(f'修复失败：{e}')
"

# 如果修复失败，重新初始化
rm optimization_data.db
python3 setup_qa_database.py
```

---

## 📞 **获取帮助**

### **报告问题前**
1. ✅ **检查此故障排除指南**
2. ✅ **运行诊断检查表**
3. ✅ **搜索现有GitHub问题**
4. ✅ **使用最小示例测试**

### **如何报告问题**
报告问题时，请包含：

```bash
# 系统信息
python3 --version
pip list | grep -E "(mcp|dspy|sentence)"
uname -a

# 错误日志
tail -n 50 debug.log

# 配置
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# 测试用例
echo "重现问题的最小提示"
```

### **支持渠道**
- 🐛 **GitHub Issues**：技术错误和功能请求
- 📚 **文档**：[用户指南](user-guide.md)详细使用说明
- ⚡ **快速帮助**：[快速入门](quick-start.md)基本设置

---

## ✅ **System Health Check Script**

Save this as `health_check.sh` for automated diagnostics:

```bash
#!/bin/bash
echo "🔍 MCP Prompt Optimizer Health Check"
echo "=================================="

# Check Python
python3 --version && echo "✅ Python OK" || echo "❌ Python issue"

# Check venv
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment active: $VIRTUAL_ENV"
else
    echo "⚠️  No virtual environment detected"
fi

# Check dependencies
pip show mcp >/dev/null 2>&1 && echo "✅ MCP installed" || echo "❌ MCP missing"
pip show dspy-ai >/dev/null 2>&1 && echo "✅ DSPy installed" || echo "❌ DSPy missing"

# Check files
[ -f prompt_optimizer.py ] && echo "✅ Main server file exists" || echo "❌ Server file missing"
[ -f optimization_data.db ] && echo "✅ Database exists" || echo "⚠️  Database will be created"

# Check Claude config
if [ -f ~/Library/Application\ Support/Claude/claude_desktop_config.json ]; then
    echo "✅ Claude Desktop config exists"
    grep -q "prompt-optimizer" ~/Library/Application\ Support/Claude/claude_desktop_config.json && 
        echo "✅ MCP server configured" || echo "❌ MCP server not configured"
else
    echo "❌ Claude Desktop config missing"
fi

echo "=================================="
echo "🎯 Health check complete!"
```

**Run with:** `chmod +x health_check.sh && ./health_check.sh`

---

**🚀 Most issues can be resolved by following this guide. For persistent problems, please report them with diagnostic information included.**