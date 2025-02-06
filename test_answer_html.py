from hypothesis import given, strategies as st
from howdoi.howdoi import _get_answer_from_html

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
    
    if has_code:
        # Add some code blocks
        num_code_blocks = draw(st.integers(min_value=1, max_value=3))
        for _ in range(num_code_blocks):
            code = draw(code_content)
            code_type = draw(st.sampled_from(['pre', 'code']))
            answer_parts.append(f'<{code_type}>{code}</{code_type}>')
            
        # Maybe add some text between code blocks
        if draw(st.booleans()):
            text = draw(text_content)
            answer_parts.append(f'<p>{text}</p>')
    else:
        # Just text content
        text = draw(text_content)
        answer_parts.append(f'<p>{text}</p>')
    
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
    
    return answer_html

@given(answer_html(), st.booleans())
def test_get_answer_from_html(html, display_full_answer):
    answer, tags = _get_answer_from_html(html, display_full_answer)
    
    # Basic validation
    assert isinstance(answer, str)
    assert isinstance(tags, list)
    assert all(isinstance(tag, str) for tag in tags)
    
    # Answer should not be empty
    assert answer != ''
    
    # If no answer found, should return NO_ANSWER_MSG
    if answer == 'NO_ANSWER_MSG':
        assert not any(tag in html for tag in ['<pre>', '<code>'])