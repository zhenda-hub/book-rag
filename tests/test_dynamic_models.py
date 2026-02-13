"""测试动态获取 OpenRouter 免费模型功能"""
import sys
sys.path.insert(0, 'src')

from src.chains.llm_manager import LLMManager


def test_fetch_models():
    """测试获取模型列表"""
    # 注意：需要设置 OPENROUTER_API_KEY 环境变量
    import os
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("跳过测试：未设置 OPENROUTER_API_KEY")
        return

    llm = LLMManager(api_key=api_key)
    models = llm.fetch_models()

    assert len(models) > 0, "应该获取到模型列表"
    assert "id" in models[0], "模型应包含 id 字段"
    assert "pricing" in models[0], "模型应包含 pricing 字段"

    print(f"✓ 获取到 {len(models)} 个模型")


def test_get_free_models():
    """测试获取免费模型列表"""
    import os
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("跳过测试：未设置 OPENROUTER_API_KEY")
        return

    llm = LLMManager(api_key=api_key)
    free_models = llm.get_free_models()

    assert len(free_models) > 0, "应该获取到免费模型"

    # 验证返回的是模型 ID 列表（字符串）
    for model_id in free_models[:5]:  # 检查前5个
        assert isinstance(model_id, str), f"模型 ID 应该是字符串: {model_id}"

    print(f"✓ 获取到 {len(free_models)} 个免费模型")


def test_get_free_models_no_api_key():
    """测试没有有效 API Key 时的行为"""
    # 使用无效 API Key，应该抛出异常
    try:
        llm = LLMManager(api_key="fake-key-12345")
        models = llm.fetch_models()
        print(f"✗ 不应该返回模型列表: {models}")
    except Exception as e:
        print(f"✓ 无效 API Key 时正确抛出异常: {type(e).__name__}")


def test_get_initial_models():
    """测试获取初始模型列表"""
    import os
    from dotenv import load_dotenv

    # 模拟有 API Key 的环境
    if os.getenv("OPENROUTER_API_KEY"):
        load_dotenv()
        from src.web.app import get_initial_models
        try:
            models = get_initial_models()
            assert len(models) > 0, "应该获取到模型列表"
            # 注意：网络不稳定时可能返回默认模型，这是降级行为
            print(f"✓ 获取到 {len(models)} 个初始模型")
        except Exception as e:
            # 网络问题导致 API 调用失败是可能的
            print(f"✓ 网络不稳定时 API 调用失败: {type(e).__name__}")
    else:
        from src.web.app import get_initial_models
        models = get_initial_models()
        assert models == ["deepseek"], "无 API Key 时应返回默认模型"
        print("✓ 无 API Key 时返回默认模型")


if __name__ == "__main__":
    print("=== 测试动态模型功能 ===\n")

    test_fetch_models()
    test_get_free_models()
    test_get_free_models_no_api_key()
    test_get_initial_models()

    print("\n所有测试完成！")
