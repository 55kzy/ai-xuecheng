# -*- coding: utf-8 -*-
"""
AI学程 自适应摸底引擎
核心逻辑：一道一出，动态调整，精准画像
"""
import json, os, glob, copy, random
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(r'D:\AI学程')
QA_DIR = BASE_DIR / '01_题库'
DATA_DIR = BASE_DIR / '04_客户数据'
TEMPLATE_DIR = BASE_DIR / '02_课程模板'

DIMENSIONS = ['K', 'P', 'T', 'L', 'C']
DIM_LABEL = {'K':'工具认知','P':'提示词','T':'技术门槛','L':'信息素养','C':'概念理解'}
TYPES = ['G', 'S', 'P', 'T', 'H', 'C']
TYPE_LABEL = {'G':'梯度型','S':'情景型','P':'偏好型','T':'两难型','H':'习惯型','C':'概念型'}


# ============================================================
# 1. 题库加载
# ============================================================
class QuestionBank:
    """加载和管理题库"""
    def __init__(self):
        self.questions = []       # 所有题目
        self.by_direction = defaultdict(list)   # 按方向索引
        self.by_id = {}           # 按ID索引
    
    def load(self, qa_dir=None):
        qa_dir = qa_dir or QA_DIR
        for d in sorted(os.listdir(qa_dir)):
            dp = os.path.join(qa_dir, d)
            if not os.path.isdir(dp):
                continue
            for f in sorted(glob.glob(os.path.join(dp, '*.json'))):
                with open(f, 'r', encoding='utf-8') as fh:
                    data = json.load(fh)
                if not isinstance(data, list):
                    continue
                for q in data:
                    q['_dir'] = d  # 记来源方向
                    self.questions.append(q)
                    self.by_id[q['id']] = q
                    dir_key = d.split('_')[0] if '_' in d else d
                    # 也加入交叉方向
                    self.by_direction[dir_key].append(q)
                    if '交叉' in d:
                        self.by_direction['CROSS'].append(q)
        
        # 反向索引：按(方向, 维度, 题型)分组
        self.index = defaultdict(list)
        for q in self.questions:
            dirs = q.get('direction', [])
            for d in dirs:
                key = (d, q['dimension'], q['type'])
                self.index[key].append(q)
        
        print(f'[题库] 加载 {len(self.questions)} 题, 来自 {len(set(q["_dir"] for q in self.questions))} 个方向')
        return self
    
    def find(self, direction=None, dimension=None, qtype=None, exclude_ids=None):
        """按条件筛选题目"""
        exclude_ids = exclude_ids or set()
        candidates = []
        for q in self.questions:
            if q['id'] in exclude_ids:
                continue
            if direction and direction not in q.get('direction', []):
                continue
            if dimension and q.get('dimension') != dimension:
                continue
            if qtype and q.get('type') != qtype:
                continue
            candidates.append(q)
        return candidates


# ============================================================
# 2. 客户画像
# ============================================================
class CustomerProfile:
    """追踪客户画像 五维(K/P/T/L/C) + 置信度"""
    def __init__(self, directions, name=None):
        self.name = name or '匿名'
        self.directions = directions  # 选择的方向列表, 如 ['A','C']
        self.scores = {d: [] for d in DIMENSIONS}  # 每题得分原始记录
        self.asked_questions = []  # 已问题目ID列表
        self.used_types = []       # 已用题型
        self.total_asked = 0
    
    def add_answer(self, question, option_score):
        """记录一道题的作答"""
        dim = question['dimension']
        self.scores[dim].append(option_score)
        self.asked_questions.append(question['id'])
        if question['type'] not in self.used_types:
            self.used_types.append(question['type'])
        self.total_asked += 1
    
    def get_dimension_score(self, dim):
        """获取某维度的平均分 (0-3)"""
        vals = self.scores[dim]
        if not vals:
            return None
        return sum(vals) / len(vals)
    
    def get_dimension_count(self, dim):
        """某维度答了多少题"""
        return len(self.scores[dim])
    
    def get_all_scores(self):
        """获取所有维度评分"""
        return {d: self.get_dimension_score(d) for d in DIMENSIONS}
    
    def get_confidence(self):
        """整体置信度 (0-1)"""
        scored_dims = sum(1 for d in DIMENSIONS if len(self.scores[d]) >= 2)
        return scored_dims / len(DIMENSIONS)
    
    def needs_more_questions(self, max_questions=6, min_questions=3):
        """判断是否还需要继续出题"""
        if self.total_asked >= max_questions:
            return False
        if self.total_asked < min_questions:
            return True
        # 置信度≥80%且至少3个维度有2题以上 → 可以停
        if self.get_confidence() >= 0.8 and sum(1 for d in DIMENSIONS if len(self.scores[d]) >= 2) >= 3:
            return False
        return True
    
    def get_missing_dimensions(self):
        """返回还没测够的维度（少于1题）"""
        return [d for d in DIMENSIONS if len(self.scores[d]) < 1]
    
    def get_low_confidence_dimensions(self):
        """返回置信度低的维度（只有1题或不稳定）"""
        return [d for d in DIMENSIONS if len(self.scores[d]) < 2]
    
    def get_profile_summary(self):
        """生成画像摘要"""
        scores = self.get_all_scores()
        lines = []
        for d in DIMENSIONS:
            s = scores[d]
            if s is None:
                lines.append(f'  {DIM_LABEL[d]}: 未测')
            else:
                level = '低' if s < 1 else ('中' if s < 2 else '高')
                lines.append(f'  {DIM_LABEL[d]}: {s:.1f}/3 ({level}) [{self.get_dimension_count(d)}题]')
        return '\n'.join(lines)
    
    def to_dict(self):
        """序列化"""
        return {
            'name': self.name,
            'directions': self.directions,
            'scores': {d: v for d, v in self.scores.items()},
            'asked': self.asked_questions,
            'used_types': self.used_types,
            'total_asked': self.total_asked,
        }
    
    @classmethod
    def from_dict(cls, data):
        p = cls(data['directions'], data.get('name'))
        p.scores = data['scores']
        p.asked_questions = data['asked']
        p.used_types = data['used_types']
        p.total_asked = data['total_asked']
        return p


# ============================================================
# 3. 自适应出题引擎（核心）
# ============================================================
class AdaptiveEngine:
    """
    核心出题引擎 — 根据客户画像动态选题
    
    策略：
    1. 初期(0-2题): 先测K(工具认知)和H/P(习惯偏好) 暖场
    2. 中间(2-4题): 填补缺失维度，轮换题型
    3. 后期(4-6题): 补全低置信维度，提高画像精度
    4. 终止: 达到6题 或 置信度≥80%
    """
    def __init__(self, question_bank):
        self.qb = question_bank
    
    def select_next(self, profile):
        """
        核心：根据当前画像，选择下一道题
        返回 Question dict 或 None（已结束）
        """
        if not profile.needs_more_questions():
            return None
        
        exclude = set(profile.asked_questions)
        dirs = profile.directions
        
        # ---- 阶段一：确定选题优先级 ----
        missing_dims = profile.get_missing_dimensions()
        low_conf_dims = profile.get_low_confidence_dimensions()
        used_types = profile.used_types
        available_types = [t for t in TYPES if t not in used_types]
        
        # 确定要测的维度和题型
        target_dim = None
        target_type = None
        
        # 优先级1: 还有未测维度 — 按得分排序（低分优先，同分随机）
        if missing_dims:
            # 把未测维度按已有得分排序：有得分的按得分升序，没得分的打乱
            scored_missing = []
            unscored_missing = []
            for d in missing_dims:
                s = profile.get_dimension_score(d)
                if s is not None:
                    scored_missing.append((s, d))
                else:
                    unscored_missing.append(d)
            
            random.shuffle(unscored_missing)
            scored_missing.sort(key=lambda x: x[0])  # 低分优先
            missing_sorted = [d for _, d in scored_missing] + unscored_missing
            target_dim = missing_sorted[0]
            # 用还没用过的题型，题型用完就用G
            target_type = available_types[0] if available_types else 'G'
        
        # 优先级2: 还有低置信维度 — 得分最低的优先补
        elif low_conf_dims:
            # 低置信维度也按得分排序
            scored_low = [(profile.get_dimension_score(d) or 1.5, d) for d in low_conf_dims]
            scored_low.sort(key=lambda x: x[0])
            target_dim = scored_low[0][1]
            target_type = available_types[0] if available_types else 'G'
            # 如果可用题型用完了且低置信维度还差题，用G
            if not available_types and profile.get_dimension_count(target_dim) < 2:
                target_type = 'G'
        
        # 优先级3: 都没问题？补全题型多样性
        elif available_types:
            # 挑置信度最低的维度
            target_dim = self._pick_lowest_dim(profile)
            target_type = available_types[0]
        
        # 优先级4: 随机抽一个还没考过的组合
        else:
            target_dim = self._pick_lowest_dim(profile)
            target_type = 'G'
        
        # ---- 阶段二：选题 ----
        candidates = self._find_question(dirs, target_dim, target_type, profile)
        
        if not candidates:
            # 容错：放宽条件再试一次
            candidates = self._find_question(dirs, target_dim, None, profile)
        
        if not candidates:
            # 实在找不到，随便挑一道没做过的
            candidates = self.qb.find(exclude_ids=exclude)
        
        if not candidates:
            return None  # 题库空了
        
        return random.choice(candidates)
    
    def _find_question(self, dirs, dim, qtype, profile):
        """按条件找合适的题"""
        exclude = set(profile.asked_questions)
        
        # 先尝试匹配每个方向
        for d in dirs:
            cond = {'dimension': dim, 'exclude_ids': exclude}
            if qtype:
                cond['qtype'] = qtype
            candidates = self.qb.find(direction=d, **cond)
            if candidates:
                return candidates
        
        # 如果有交叉方向，试试交叉题
        candidates = self.qb.find(direction='CROSS', dimension=dim, qtype=qtype, exclude_ids=exclude)
        if candidates:
            return candidates
        
        return []
    
    def _pick_lowest_dim(self, profile):
        """挑当前分数最低的维度作为补测目标"""
        scored = []
        for d in DIMENSIONS:
            s = profile.get_dimension_score(d)
            if s is not None:
                scored.append((s, d))
        if not scored:
            return random.choice(DIMENSIONS)
        scored.sort()
        return scored[0][1]
    
    def evaluate_answer(self, question, option_indices):
        """根据选择的选项返回对应维度的得分
        
        单题: option_indices 是 int
        多选(question.get('multiple')==True): option_indices 是 list[int], 等权重平均
        """
        is_multiple = question.get('multiple', False)
        
        if is_multiple:
            # 多选：等权重平均所有选中选项的得分
            if not isinstance(option_indices, list):
                option_indices = [option_indices]
            dim = question['dimension']
            total = 0.0
            count = 0
            for idx in option_indices:
                if 0 <= idx < len(question['options']):
                    total += question['options'][idx]['score'].get(dim, 0)
                    count += 1
            return total / count if count > 0 else None
        else:
            # 单选：原有逻辑
            if isinstance(option_indices, list):
                option_indices = option_indices[0] if option_indices else 0
            if option_indices < 0 or option_indices >= len(question['options']):
                return None
            opt = question['options'][option_indices]
            dim = question['dimension']
            return opt['score'].get(dim, 0)


# ============================================================
# 4. 课程推荐
# ============================================================
class CourseRecommender:
    """根据画像推荐课程"""
    
    @staticmethod
    def recommend(profile):
        """生成课程推荐"""
        scores = profile.get_all_scores()
        dirs = profile.directions
        
        # 对每个方向给出学习建议
        recommendations = []
        
        # 基于维度分数的通用建议
        if scores.get('K', 0) < 1.5:
            recommendations.append('🔧 工具认知有待提升 — 先了解AI能做什么、各工具的特点')
        if scores.get('P', 0) < 1.5:
            recommendations.append('✍️ 提示词技能可以加强 — 学习如何给AI清晰的指令')
        if scores.get('L', 0) < 1.5:
            recommendations.append('🔍 信息素养需要培养 — 学会验证AI输出的准确性')
        if scores.get('T', 0) < 1.5:
            recommendations.append('📈 技术门槛较高 — 建议从零门槛工具开始入门')
        if scores.get('C', 0) < 1.5:
            recommendations.append('🧠 概念理解可以加深 — 了解AI的运作原理帮助你更好使用')
        
        # 方向专属建议
        dir_suggestions = {
            'A': '从日常生活场景开始，解决实际问题',
            'B': '聚焦职场效率提升，找到你工作中的痛点',
            'C': '自媒体创作是你的主方向，重点攻克内容生产和优化',
            'D': '变现方向需要结合工具能力和市场需求',
            'E': '技术方向需要系统学习，从基础开始',
            'F': '学术方向关注文献管理和研究辅助',
            'G': '全面了解AI，建立完整的认知框架',
        }
        
        dir_advice = []
        for d in dirs:
            if d in dir_suggestions:
                dir_advice.append(dir_suggestions[d])
        
        return {
            'directions': dirs,
            'level': '入门' if max(v or 0 for v in scores.values()) < 1.5 else 
                     ('进阶' if max(v or 0 for v in scores.values()) < 2.5 else '高级'),
            'recommendations': recommendations,
            'direction_advice': dir_advice,
            'focus_dimensions': [d for d in DIMENSIONS if (scores.get(d, 0) or 0) < 1.5],
        }


# ============================================================
# 5. CLI 交互界面
# ============================================================
def cli_session():
    """命令行交互摸底"""
    print('\n' + '=' * 50)
    print('  🧠 AI学程 — 自适应摸底引擎')
    print('=' * 50)
    
    # 1. 加载题库
    qb = QuestionBank().load()
    engine = AdaptiveEngine(qb)
    
    # 2. 选方向
    print('\n📌 请选择学习方向（可多选，用空格隔开）：')
    print('  A 日常生活  B 职场应用  C 自媒体  D 搞钱变现')
    print('  E 技术开发  F 学术研究  G 全面了解')
    dir_choice = input('\n输入方向字母（如 A C）: ').strip().upper().split()
    valid_dirs = [d for d in dir_choice if d in 'ABCDEFG']
    if not valid_dirs:
        valid_dirs = ['A']
    print(f'  已选方向: {", ".join(valid_dirs)}')
    
    # 3. 摸底
    profile = CustomerProfile(valid_dirs)
    print('\n📝 开始摸底（共3-6题，做完为止）\n')
    
    while True:
        q = engine.select_next(profile)
        if q is None:
            break
        
        print(f'[第{profile.total_asked+1}题] {q["text"]}')
        for i, opt in enumerate(q['options']):
            print(f'  {i+1}. {opt["text"]}')
        
        while True:
            try:
                choice = input(f'\n你的选择 (1-{len(q["options"])}): ').strip()
                idx = int(choice) - 1
                if 0 <= idx < len(q['options']):
                    break
            except:
                pass
            print(f'请输入 1-{len(q["options"])}')
        
        score = engine.evaluate_answer(q, idx)
        profile.add_answer(q, score)
        
        # 显示当前画像进度
        print(f'  → 当前画像: {profile.get_profile_summary()}')
        print()
    
    # 4. 出结果
    print('=' * 50)
    print('  ✅ 摸底完成！')
    print('=' * 50)
    print(f'\n总答题数: {profile.total_asked}')
    print(f'\n📊 客户画像:')
    print(profile.get_profile_summary())
    
    recommender = CourseRecommender()
    result = recommender.recommend(profile)
    
    print(f'\n📋 综合水平: {result["level"]}')
    if result['recommendations']:
        print('\n💡 学习建议:')
        for r in result['recommendations']:
            print(f'  {r}')
    if result['direction_advice']:
        print('\n🎯 方向建议:')
        for a in result['direction_advice']:
            print(f'  {a}')
    
    # 5. 保存
    os.makedirs(DATA_DIR, exist_ok=True)
    save_path = os.path.join(DATA_DIR, f'{profile.name}.json')
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(profile.to_dict(), f, ensure_ascii=False, indent=2)
    print(f'\n💾 画像已保存到: {save_path}')
    
    return profile, result


# ============================================================
# 6. 程序化接口 (供外部调用)
# ============================================================
class Session:
    """一次摸底会话，可以一问一答逐步进行"""
    def __init__(self, directions, name=None, qb=None):
        if qb is None:
            qb = QuestionBank().load()
        self.qb = qb
        self.engine = AdaptiveEngine(qb)
        self.profile = CustomerProfile(directions, name)
        self.current_question = None
        self.history = []  # [(question, option_index, score), ...]
    
    def next_question(self):
        """获取下一道题"""
        self.current_question = self.engine.select_next(self.profile)
        return self.current_question
    
    def answer(self, option_indices):
        """提交答案
        
        option_indices: int (单题) 或 list[int] (多题)
        """
        if self.current_question is None:
            return None
        score = self.engine.evaluate_answer(self.current_question, option_indices)
        self.profile.add_answer(self.current_question, score)
        self.history.append((self.current_question, option_indices, score))
        self.current_question = None
        return score
    
    def go_back(self):
        """退回上一题，返回上一题题目"""
        if not self.history:
            return None
        # 弹出最后一题记录
        last_q, last_opt, last_score = self.history.pop()
        # 从画像中移除该题记录
        dim = last_q['dimension']
        qt = last_q['type']
        qid = last_q['id']
        # 从scores中移除最后一个该维度的记录
        dim_scores = self.profile.scores[dim]
        if dim_scores:
            dim_scores.pop()
        # 从asked_questions移除该ID
        if qid in self.profile.asked_questions:
            self.profile.asked_questions.remove(qid)
        # 从used_types中检查是否还需要保留该题型
        still_has_type = any(
            qid2 != qid and qt in [q2.get('type') for q2 in self.qb.questions if q2['id'] == qid2]
            for qid2 in self.profile.asked_questions
        )
        if not still_has_type and qt in self.profile.used_types:
            self.profile.used_types.remove(qt)
        self.profile.total_asked -= 1
        
        # 设置current_question为上一题
        self.current_question = last_q
        return last_q
    
    def can_go_back(self):
        """是否可以退回"""
        return len(self.history) > 0
    
    def is_done(self):
        """摸底是否完成"""
        return not self.profile.needs_more_questions()
    
    def get_results(self):
        """获取摸底结果"""
        recommender = CourseRecommender()
        return {
            'profile': self.profile,
            'recommendation': recommender.recommend(self.profile),
        }


# ============================================================
# 7. main
# ============================================================
if __name__ == '__main__':
    # 运行交互式摸底
    profile, result = cli_session()
    
    print('\n' + '=' * 50)
    print('感谢使用 AI学程！明天见 🥴')
    print('=' * 50)
