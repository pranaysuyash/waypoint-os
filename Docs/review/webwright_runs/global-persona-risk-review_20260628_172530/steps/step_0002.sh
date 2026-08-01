cd /Users/pranay/Projects/travel_agency_agent/Docs/review/webwright_runs/global-persona-risk-review_20260628_172530 && cat > plan.md <<'EOF'
# Critical Points
- [ ] CP1: Log in successfully with newuser@test.com / testpass123.
- [ ] CP2: Open the workbench after login.
- [ ] CP3: Create a new trip or clearly reuse an existing trip suitable for this scenario.
- [ ] CP4: Set destination to Cape Town.
- [ ] CP5: Set travel timing to March.
- [ ] CP6: Set group size to exactly 42 travelers.
- [ ] CP7: Capture that the scenario is for a leadership offsite / events team from London.
- [ ] CP8: Set budget to GBP 68,000.
- [ ] CP9: Apply premium hotel requirement.
- [ ] CP10: Apply meeting room requirement.
- [ ] CP11: Apply airport transfers requirement.
- [ ] CP12: Apply flexible dates requirement.
- [ ] CP13: Apply child-free requirement.
- [ ] CP14: Apply sunset cruise requirement.
- [ ] CP15: Apply winery visit requirement.
- [ ] CP16: Apply VIP airport fast track requirement.
- [ ] CP17: Submit or advance the workflow so the app processes the completed trip request.
- [ ] CP18: Reach the Risk Review stage/page in the app.
- [ ] CP19: In the safety section, verify the UI shows the actual leaked terms or jargon, not only a generic failure message.
- [ ] CP20: Capture evidence needed to document what is good, bad, missing, and workflow gaps observed during the end-to-end flow.
EOF
python - <<'PY'
import json
from pathlib import Path
root = Path('/Users/pranay/Projects/travel_agency_agent/Docs/review/webwright_runs/global-persona-risk-review_20260628_172530')
critical_points = '''1. CP1: Log in successfully with newuser@test.com / testpass123.
2. CP2: Open the workbench after login.
3. CP3: Create a new trip or clearly reuse an existing trip suitable for this scenario.
4. CP4: Set destination to Cape Town.
5. CP5: Set travel timing to March.
6. CP6: Set group size to exactly 42 travelers.
7. CP7: Capture that the scenario is for a leadership offsite / events team from London.
8. CP8: Set budget to GBP 68,000.
9. CP9: Apply premium hotel requirement.
10. CP10: Apply meeting room requirement.
11. CP11: Apply airport transfers requirement.
12. CP12: Apply flexible dates requirement.
13. CP13: Apply child-free requirement.
14. CP14: Apply sunset cruise requirement.
15. CP15: Apply winery visit requirement.
16. CP16: Apply VIP airport fast track requirement.
17. CP17: Submit or advance the workflow so the app processes the completed trip request.
18. CP18: Reach the Risk Review stage/page in the app.
19. CP19: In the safety section, verify the UI shows the actual leaked terms or jargon, not only a generic failure message.
20. CP20: Capture evidence needed to document what is good, bad, missing, and workflow gaps observed during the end-to-end flow.'''
task_desc = 'Log in with newuser@test.com / testpass123, open the workbench, create or reuse a new trip, and simulate this exact customer scenario end-to-end: London-based events team of 42 wants Cape Town in March for a leadership offsite, GBP 68k budget, premium hotel, meeting room, airport transfers, flexible dates, child-free, sunset cruise, winery visit, VIP airport fast track. Verify the app reaches Risk Review and the safety section lists the actual leaked terms or jargon instead of only a generic failure. Document what is good, bad, missing, and any workflow gaps you see.'
config = {
  'image_judge_system_prompt': 'You are a harsh evaluator of web automation evidence. Return ONLY two labelled lines exactly in this format:\nReasoning: <1-2 sentences describing what the screenshot shows and which critical points it provides evidence for or against>\nScore: <integer 1-5, where 5 = this screenshot clearly evidences a critical point and 1 = this screenshot contains no relevant evidence>\nBe strict: if evidence is ambiguous, partially occluded, or indirect, score low.',
  'image_judge_user_prompt': f'Task description:\n{task_desc}\n\nCritical points to consider for this single screenshot:\n{critical_points}\n\nEvaluate this one image against ALL critical points, not just the most obvious one. Be harsh when evidence is ambiguous, partially hidden, or only implied. Score 5 only when the image clearly proves one or more critical points.',
  'final_verdict_system_prompt': 'You are a harsh aggregated judge of whether a web task was truly completed. You will receive the task description, critical points, the action history log, per-image reasonings, and all screenshots. First provide a Thoughts: block that explicitly evaluates every critical point and whether the combined evidence satisfies it. Then end your reply with EXACTLY one final line on its own: Status: success OR Status: failure. Be strict: missing, ambiguous, or indirect evidence means failure.',
  'final_verdict_user_prompt': f'Task description:\n{task_desc}\n\nCritical points:\n{critical_points}\n\nAction history log:\n{{action_history_log}}\n\nPer-image reasonings:\n{{image_reasonings}}\n\nUsing the complete action log, all screenshot reasonings, and the attached screenshots, determine whether every critical point is satisfied. Also assess whether the evidence documents what is good, bad, missing, and workflow gaps observed in the flow. If the app reaches Risk Review but the safety section does not visibly list actual leaked terms or jargon, treat that as a failure for CP19. Respond with a Thoughts: block that covers every critical point, then end with the required status line.'
}
(root / 'self_reflect_config.json').write_text(json.dumps(config, indent=2))
print('WROTE', root / 'self_reflect_config.json')
PY
ls -la plan.md self_reflect_config.json && sed -n '1,220p' plan.md && echo '---CONFIG---' && sed -n '1,260p' self_reflect_config.json
