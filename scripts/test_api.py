import os
import requests
import json
import time

API_BASE = "http://127.0.0.1:8080"

def wait_for_server():
    print("等待 API 服务启动...")
    for _ in range(10):
        try:
            r = requests.get(f"{API_BASE}/health")
            if r.status_code == 200:
                print("✅ 服务已启动\n")
                return True
        except requests.ConnectionError:
            time.sleep(1)
    return False

def test_match_and_execute():
    # 1. 模拟用户提问，触发 Match 阶段
    query = "帮我整理一下最近关于房地产的市场情绪，看看有没有利好政策"
    print(f"👤 用户输入: {query}")
    
    print("🔄 [阶段1: Match] 请求 /chat/query...")
    resp = requests.post(f"{API_BASE}/chat/query", json={"query": query})
    if resp.status_code != 200:
        print(f"❌ Match 请求失败: {resp.text}")
        return
        
    data = resp.json()
    candidates = data.get("candidates", [])
    if not candidates:
        print("❌ 未匹配到任何 Flow")
        return
        
    top_flow = candidates[0]
    flow_id = top_flow["flow_id"]
    print(f"✅ 匹配成功! 推荐 Flow: [{flow_id}] - {top_flow['name']} (匹配理由: {top_flow['reason']})")
    
    # 提取的参数
    extracted_params = data.get("intent", {}).get("extracted_params", {})
    topic = extracted_params.get("analysis_topic", "房地产")
    
    print("\n🔄 [阶段2: Confirm] 模拟用户确认执行该 Flow...")
    inputs = {
        "analysis_topic": topic,
        "lookback_days": 7,
        "output_path": "report_api_test.md"
    }
    
    print("🔄 [阶段3: Execute] 请求 /flow/execute...")
    resp = requests.post(f"{API_BASE}/flow/execute", json={
        "flow_id": flow_id,
        "inputs": inputs
    })
    
    if resp.status_code != 200:
        print(f"❌ Execute 请求失败: {resp.text}")
        return
        
    exec_data = resp.json().get("execution", {})
    status = exec_data.get("status")
    
    if status == "success":
        print("✅ 执行成功! 步骤明细:")
        for step in exec_data.get("step_results", []):
            print(f"  - [{step['step_id']}]: {step['status']}")
        print("\n🎉 方案B 全链路测试完成！")
    else:
        print("❌ 执行失败:")
        for step in exec_data.get("step_results", []):
            if step['status'] == 'failed':
                print(f"  - 失败步骤 [{step['step_id']}]: {step.get('error')}")

if __name__ == "__main__":
    if not wait_for_server():
        print("❌ 无法连接到服务，请先在另一个终端运行: uvicorn app.main:app --reload --port 8080")
    else:
        test_match_and_execute()
