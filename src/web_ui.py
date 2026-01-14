# 小游探 Web UI - Gradio界面
"""
简单实用的Web界面，展示Agent协作过程
"""

import asyncio
import gradio as gr
from datetime import datetime
from typing import List, Tuple
import sys
from pathlib import Path

# 添加项目根目录到路径
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from loguru import logger
from src.agents.router_agent import RouterAgent
from src.agents.live_monitor_agent import LiveMonitorAgent
from src.agents.briefing_agent import BriefingAgent
from src.agents.data_source_agent import DataSourceAgent
from src.utils.common import setup_logger, load_env


class YouGameWebUI:
    """小游探Web界面"""
    
    def __init__(self):
        setup_logger()
        load_env()
        
        self.router = None
        self.live_monitor = None
        self.briefing_agent = None
        self.data_source_agent = None
        
        self.chat_history = []
        self.agent_logs = []
        
    async def initialize(self):
        """初始化所有Agent"""
        logger.info("初始化小游探系统...")
        
        # 创建Agent
        self.data_source_agent = DataSourceAgent()
        self.live_monitor = LiveMonitorAgent()
        self.briefing_agent = BriefingAgent()
        self.router = RouterAgent()
        
        # 注册Agent
        self.router.register_agent("live_monitor", self.live_monitor)
        self.router.register_agent("briefing_agent", self.briefing_agent)
        self.router.register_agent("data_source", self.data_source_agent)
        
        # 启动Agent
        await self.data_source_agent.on_startup()
        await self.live_monitor.on_startup()
        await self.briefing_agent.on_startup()
        await self.router.on_startup()
        
        logger.info("✅ 系统初始化完成")
        
    async def process_query(self, user_input: str, history: List) -> Tuple[List, str]:
        """处理用户查询"""
        if not user_input.strip():
            return history, ""
        
        # 添加用户消息到历史
        history.append((user_input, None))
        
        # 记录Agent日志
        log_entry = f"[{datetime.now().strftime('%H:%M:%S')}] 用户查询: {user_input}\n"
        self.agent_logs.append(log_entry)
        
        try:
            # 处理查询
            result = await self.router.smart_process(
                user_input,
                self.router.QueryContext(
                    user_id="web_user",
                    session_id="web_session",
                    timestamp=datetime.now()
                )
            )
            
            # 记录Agent使用情况
            agents_used = result.get("agents_used", ["router"])
            intent = result.get("intent", "未知")
            confidence = result.get("confidence", 0.0)
            processing_time = result.get("processing_time", 0.0)
            
            log_entry = f"[{datetime.now().strftime('%H:%M:%S')}] 意图: {intent} (置信度: {confidence:.2f})\n"
            log_entry += f"[{datetime.now().strftime('%H:%M:%S')}] 使用Agent: {', '.join(agents_used)}\n"
            log_entry += f"[{datetime.now().strftime('%H:%M:%S')}] 处理时间: {processing_time:.2f}s\n"
            self.agent_logs.append(log_entry)
            
            # 更新历史
            response = result.get("response", "抱歉，处理失败")
            history[-1] = (user_input, response)
            
            # 生成Agent日志显示
            agent_log_display = "".join(self.agent_logs[-10:])  # 只显示最近10条
            
            return history, agent_log_display
            
        except Exception as e:
            logger.error(f"处理查询失败: {e}")
            error_msg = f"❌ 处理失败: {str(e)}"
            history[-1] = (user_input, error_msg)
            
            log_entry = f"[{datetime.now().strftime('%H:%M:%S')}] 错误: {str(e)}\n"
            self.agent_logs.append(log_entry)
            agent_log_display = "".join(self.agent_logs[-10:])
            
            return history, agent_log_display
    
    def get_demo_queries(self) -> List[str]:
        """获取演示查询"""
        return [
            "你好",
            "Faker在直播吗？",
            "生成今日简报",
            "系统状态",
            "最近有什么热门游戏？"
        ]
    
    def create_interface(self):
        """创建Gradio界面"""
        
        with gr.Blocks(title="小游探 - 游戏圈AI助手", theme=gr.themes.Soft()) as demo:
            gr.Markdown("""
            # 🎮 小游探 - 游戏圈AI助手
            
            基于OpenAgents的多Agent协作系统，智能查询游戏直播和圈内动态
            """)
            
            with gr.Row():
                with gr.Column(scale=2):
                    # 聊天界面
                    chatbot = gr.Chatbot(
                        label="对话",
                        height=400,
                        show_label=True,
                        avatar_images=(None, "🤖")
                    )
                    
                    with gr.Row():
                        msg = gr.Textbox(
                            label="输入你的问题",
                            placeholder="例如：Faker在直播吗？",
                            scale=4
                        )
                        submit_btn = gr.Button("发送", variant="primary", scale=1)
                    
                    # 快捷查询按钮
                    gr.Markdown("### 💡 快捷查询")
                    with gr.Row():
                        demo_btns = []
                        for query in self.get_demo_queries():
                            btn = gr.Button(query, size="sm")
                            demo_btns.append((btn, query))
                
                with gr.Column(scale=1):
                    # Agent协作日志
                    gr.Markdown("### 🤖 Agent协作日志")
                    agent_log = gr.Textbox(
                        label="实时日志",
                        lines=15,
                        max_lines=20,
                        interactive=False,
                        show_label=False
                    )
                    
                    # 系统信息
                    gr.Markdown("### 📊 系统信息")
                    system_info = gr.Markdown("""
                    - **Router Agent**: 智能路由
                    - **LiveMonitor Agent**: 直播监控
                    - **Briefing Agent**: 简报生成
                    - **DataSource Agent**: 数据源管理
                    
                    **状态**: 🟢 运行中
                    """)
            
            # 使用说明
            with gr.Accordion("📖 使用说明", open=False):
                gr.Markdown("""
                ### 功能介绍
                
                1. **直播查询**: 询问主播是否在直播，例如"Faker在直播吗？"
                2. **简报生成**: 获取游戏圈动态，例如"生成今日简报"
                3. **系统状态**: 查看系统运行状态，例如"系统状态"
                4. **智能对话**: 支持自然语言交互
                
                ### Agent协作
                
                系统使用多个Agent协同工作：
                - **Router Agent** 负责理解意图和任务分发
                - **LiveMonitor Agent** 负责监控直播状态
                - **Briefing Agent** 负责生成智能简报
                - **DataSource Agent** 负责数据获取和管理
                
                右侧的日志窗口会实时显示Agent的协作过程。
                """)
            
            # 事件处理
            def handle_submit(user_input, history):
                """处理提交"""
                return asyncio.run(self.process_query(user_input, history))
            
            # 绑定事件
            submit_btn.click(
                fn=handle_submit,
                inputs=[msg, chatbot],
                outputs=[chatbot, agent_log]
            ).then(
                fn=lambda: "",
                outputs=[msg]
            )
            
            msg.submit(
                fn=handle_submit,
                inputs=[msg, chatbot],
                outputs=[chatbot, agent_log]
            ).then(
                fn=lambda: "",
                outputs=[msg]
            )
            
            # 绑定快捷按钮
            for btn, query in demo_btns:
                btn.click(
                    fn=lambda q=query: q,
                    outputs=[msg]
                )
        
        return demo
    
    def launch(self, share=False, server_port=7860):
        """启动Web界面"""
        logger.info("启动Web界面...")
        
        # 初始化系统
        asyncio.run(self.initialize())
        
        # 创建并启动界面
        demo = self.create_interface()
        demo.launch(
            share=share,
            server_port=server_port,
            server_name="0.0.0.0"
        )


def main():
    """主函数"""
    ui = YouGameWebUI()
    ui.launch(share=False, server_port=7860)


if __name__ == "__main__":
    main()
