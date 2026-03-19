import os
import json
from app.storage.flow_repository import FlowRepository
from app.flow_engine.executor import FlowExecutor

def main():
    print("=== SW-Flow-Project 终端测试脚本 ===\n")
    
    # 1. 检查环境变量
    if not os.path.exists(".env"):
        print("❌ 错误: 未找到 .env 文件！请从 .env.example 复制为 .env 并填入真实的 LLM_API_KEY。")
        return

    # 2. 初始化仓库和执行器
    repo = FlowRepository("flows")
    executor = FlowExecutor()
    
    # 我们测试刚才更新的 "market-environment-china"
    flow_id = "market-environment-china"
    print(f"正在加载 Flow: [{flow_id}] ...")
    try:
        flow = repo.get_flow(flow_id)
        print(f"✅ 成功加载 Flow: {flow.meta.name}\n")
    except FileNotFoundError:
        print(f"❌ 错误: 找不到 Flow [{flow_id}]")
        return

    # 3. 构造模拟输入参数 (根据 flow 的 inputs 定义)
    inputs = {
        "analysis_topic": "房地产",
        "lookback_days": 7,
        "output_path": "report_test.md"
    }
    print(f"🚀 开始执行 Flow，输入参数:\n{json.dumps(inputs, ensure_ascii=False, indent=2)}\n")
    
    # 4. 执行 Flow
    result = executor.execute(flow.spec, inputs)
    
    # 5. 打印结果
    print("=== 执行结果 ===")
    print(f"最终状态: {'✅ 成功' if result.status == 'success' else '❌ 失败'}")
    print("\n[各步骤详情]:")
    for step in result.step_results:
        status_icon = "✅" if step.status == "success" else "❌"
        print(f"  {status_icon} 步骤 [{step.step_id}]: {step.status}")
        if step.error:
            print(f"      错误信息: {step.error}")

    if result.status == "success":
        print("\n🎉 测试完成！你可以检查项目目录下是否生成了对应的报告文件。")

if __name__ == "__main__":
    main()
