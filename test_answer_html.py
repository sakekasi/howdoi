from hypothesis import given, strategies as st
from howdoi.howdoi import _get_answer_from_html, NO_ANSWER_MSG

# Strategy for generating text content
text_content = st.text(alphabet=st.characters(blacklist_categories=('Cs',)), min_size=1)

# Strategy for generating code content
code_content = st.text(alphabet=st.characters(blacklist_categories=('Cs',)), min_size=1)

# Strategy for generating tags
tag = st.text(alphabet=st.characters(min_codepoint=48, max_codepoint=122), min_size=1, max_size=20)
tags = st.lists(tag, min_size=0, max_size=5)

# Strategy for generating answer HTML
@st.composite
def answer_html(draw):
    # Generate tags
    question_tags = draw(tags)
    tags_html = ''.join(f'<a class="post-tag">{t}</a>' for t in question_tags)
    
    # Decide which answer body class to use
    answer_body_cls = draw(st.sampled_from(['.js-post-body', '.post-text']))
    
    # Generate main answer content
    has_code = draw(st.booleans())
    answer_parts = []
    expected_answer_parts = []
    
    if has_code:
        # Add some code blocks
        num_code_blocks = draw(st.integers(min_value=1, max_value=3))
        for _ in range(num_code_blocks):
            code = draw(code_content)
            code_type = draw(st.sampled_from(['pre', 'code']))
            answer_parts.append(f'<{code_type}>{code}</{code_type}>')
            expected_answer_parts.append(code)
            
        # Maybe add some text between code blocks
        if draw(st.booleans()):
            text = draw(text_content)
            answer_parts.append(f'<p>{text}</p>')
            expected_answer_parts.append(text)
    else:
        # Just text content
        text = draw(text_content)
        answer_parts.append(f'<p>{text}</p>')
        expected_answer_parts.append(text)
    
    # Build the answer HTML
    answer_body_cls = answer_body_cls.lstrip('.')
    answer_html = f'''
    <div class="answercell">
        <div class="{answer_body_cls}">
            {"".join(answer_parts)}
        </div>
    </div>
    <div class="tags">
        {tags_html}
    </div>
    '''
    
    # For display_full_answer=True, we expect all parts joined with newlines
    expected_full_answer = '\n'.join(expected_answer_parts).strip()
    # For display_full_answer=False, we expect just the first code block if it exists,
    # otherwise the first text block
    expected_short_answer = (expected_answer_parts[0] if has_code else expected_answer_parts[0]).strip()
    
    return (expected_short_answer, expected_full_answer, question_tags, answer_html)

@given(answer_html(), st.booleans())
def test_get_answer_from_html(generated, display_full_answer):
    expected_short_answer, expected_full_answer, expected_tags, html = generated
    answer, tags = _get_answer_from_html(html, display_full_answer)
    
    # Basic validation
    assert isinstance(answer, str)
    assert isinstance(tags, list)
    assert all(isinstance(tag, str) for tag in tags)
    
    # Answer should not be empty unless it's NO_ANSWER_MSG
    assert answer != '' or answer == NO_ANSWER_MSG
    
    # Tags should match exactly
    assert tags == expected_tags
    
    # Answer should match expected answer based on display_full_answer
    expected = expected_full_answer if display_full_answer else expected_short_answer
    assert answer.strip() == expected.strip()