# 雪球 Token 自动检测与半自动修复

本文档说明如何通过 MCP 工具手动完成：

- 检测 `stock_individual_spot_xq` 是否因 token 过期不可用
- 人工粘贴 Cookie 后更新运行时 token 并立即验证

## 1. MCP 工具说明

新增两个 MCP tool：

- `xq_token_health_check`
  - 用于检测雪球接口可用性
  - 会返回不带 token 和（若已设置）带运行时 token 的探测结果
- `xq_token_update`
  - 可传 `token` 或完整 `cookie`
  - 若传 cookie，自动提取 `xq_a_token`
  - 设置后自动验证指定股票代码（默认 `SH600000`）

另外，`stock_individual_spot_xq` 已支持优先使用 MCP 进程内运行时 token（也可在调用时显式传 `token`）。

## 2. 部署与重启

更新代码后重建 MCP 容器：

```bash
docker compose up -d --build
```

查看 MCP 服务日志：

```bash
docker logs -f akshare-mcp-server
```

## 3. 手动检测与修复流程（MCP）

1) 调用 `xq_token_health_check`
- 示例参数：`symbol=SH600000`
- 查看返回中的 `success` 与 `data` 字段

2) 调用 `xq_token_update`
- 方式 A：直接传 token（推荐）
  - `token=<xq_a_token>`
- 方式 B：传完整 cookie
  - `cookie=<完整cookie字符串>`
- 可选：`verify_symbol=SH600000`

3) 再调用 `xq_token_health_check` 或 `stock_individual_spot_xq(symbol="SH600000")` 验证是否恢复

## 4. 失败处理与回滚

- 若更新失败：
  - 确认 cookie 中包含 `xq_a_token`
  - 检查 token 是否已过期/被风控
- 若验证失败：
  - 重试一次最新 token
  - 检查雪球账号状态（是否触发风控）
- 临时降级：
  - 使用 `stock_bid_ask_em` / `stock_individual_info_em` 作为替代数据源

## 5. 安全建议

- 不要把完整 Cookie 写入仓库或日志。
- 推荐直接通过 MCP tool 参数传 token，避免传完整 cookie。
- MCP 返回中 token 仅显示脱敏形式（前 4 后 4）。
