#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AI-Tool MCP 项目代码质量检测脚本
使用多种工具全面检测代码质量
"""

import subprocess
import sys
import os
from pathlib import Path
import json


class CodeQualityChecker:
    """代码质量检测器"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.results = {}
        
    def run_command(self, command: list, description: str) -> dict:
        """运行命令并返回结果"""
        print(f"\n{'='*60}")
        print(f"🔍 {description}")
        print(f"{'='*60}")
        
        try:
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                cwd=self.project_root
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "returncode": -1
            }
    
    def check_flake8(self):
        """Flake8 代码风格检查"""
        result = self.run_command(
            ["flake8", "core/", "services/", "server.py", "*.py",
             "--max-line-length=88", "--extend-ignore=E203,W503",
             "--exclude=.venv,__pycache__,.git"],
            "Flake8 代码风格检查"
        )
        
        if result["success"]:
            print("✅ Flake8 检查通过 - 代码风格良好")
        else:
            print("❌ Flake8 发现问题:")
            print(result["stdout"])
            
        self.results["flake8"] = result
        return result
    
    def check_pylint(self):
        """Pylint 代码质量检查"""
        result = self.run_command(
            ["pylint", "services/", "core/", "server.py",
             "--output-format=text", "--score=yes", "--disable=C0114,C0115,C0116"],
            "Pylint 代码质量检查"
        )
        
        # Pylint 总是返回非零退出码，所以我们检查输出
        if "Your code has been rated at" in result["stdout"]:
            lines = result["stdout"].split('\n')
            for line in lines:
                if "Your code has been rated at" in line:
                    print(f"📊 {line}")
                    break
        
        print(result["stdout"])
        self.results["pylint"] = result
        return result
    
    def check_bandit(self):
        """Bandit 安全检查"""
        result = self.run_command(
            ["bandit", "-r", "core/,services/", "-f", "json",
             "-x", "tests/,__pycache__/,.venv/"],
            "Bandit 安全漏洞检查"
        )
        
        if result["success"]:
            print("✅ Bandit 安全检查通过 - 未发现安全问题")
        else:
            try:
                bandit_data = json.loads(result["stdout"])
                issues = bandit_data.get("results", [])
                if issues:
                    print(f"⚠️  发现 {len(issues)} 个潜在安全问题:")
                    for issue in issues[:5]:  # 只显示前5个
                        print(f"  - {issue['test_name']}: {issue['issue_text']}")
                        print(f"    文件: {issue['filename']}:{issue['line_number']}")
            except:
                print("❌ Bandit 检查失败:")
                print(result["stderr"])
                
        self.results["bandit"] = result
        return result
    
    def check_radon_complexity(self):
        """Radon 复杂度检查"""
        result = self.run_command(
            ["radon", "cc", "core/", "services/", "server.py", "-a", "-nc"],
            "Radon 代码复杂度分析"
        )
        
        if result["success"]:
            print("📈 代码复杂度分析:")
            print(result["stdout"])
        else:
            print("❌ 复杂度分析失败")
            
        self.results["radon_complexity"] = result
        return result
    
    def check_radon_maintainability(self):
        """Radon 可维护性检查"""
        result = self.run_command(
            ["radon", "mi", "core/", "services/", "server.py", "-nc"],
            "Radon 可维护性指数分析"
        )
        
        if result["success"]:
            print("🔧 可维护性指数:")
            print(result["stdout"])
        else:
            print("❌ 可维护性分析失败")
            
        self.results["radon_maintainability"] = result
        return result
    
    def check_imports(self):
        """检查导入排序 (isort)"""
        result = self.run_command(
            ["isort", "core/", "services/", "server.py", "*.py",
             "--check-only", "--diff", "--skip=.venv"],
            "Import 排序检查"
        )
        
        if result["success"]:
            print("✅ Import 排序正确")
        else:
            print("❌ Import 排序需要修复:")
            print(result["stdout"])
            
        self.results["isort"] = result
        return result
    
    def run_all_checks(self):
        """运行所有代码质量检查"""
        print("🚀 开始 AI-Tool MCP 项目代码质量检测")
        print(f"📁 项目路径: {self.project_root.absolute()}")
        
        # 运行所有检查
        checks = [
            self.check_flake8,
            self.check_imports,
            self.check_bandit,
            self.check_radon_complexity,
            self.check_radon_maintainability,
            self.check_pylint,  # 放在最后，因为输出较多
        ]
        
        for check in checks:
            try:
                check()
            except Exception as e:
                print(f"❌ 检查失败: {e}")
        
        # 生成总结报告
        self.generate_summary()
    
    def generate_summary(self):
        """生成总结报告"""
        print(f"\n{'='*60}")
        print("📋 代码质量检测总结报告")
        print(f"{'='*60}")
        
        passed = 0
        total = len(self.results)
        
        for tool, result in self.results.items():
            status = "✅ 通过" if result.get("success", False) else "❌ 需要关注"
            print(f"{tool:20} : {status}")
            if result.get("success", False):
                passed += 1
        
        print(f"\n📊 总体评分: {passed}/{total} 项检查通过")
        
        if passed == total:
            print("🎉 恭喜！代码质量优秀！")
        elif passed >= total * 0.8:
            print("👍 代码质量良好，有少量改进空间")
        elif passed >= total * 0.6:
            print("⚠️  代码质量一般，建议进行优化")
        else:
            print("🔧 代码质量需要重点改进")


def main():
    """主函数"""
    checker = CodeQualityChecker()
    checker.run_all_checks()


if __name__ == "__main__":
    main()
