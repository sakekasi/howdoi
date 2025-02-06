from hypothesis import given, strategies as st
from howdoi.howdoi import _get_answer_from_html, NO_ANSWER_MSG

# Strategy for generating text content - exclude control chars, whitespace, and HTML-like content
text_content = st.text(
    alphabet=st.characters(blacklist_categories=('Cs', 'Cc', 'Z')),
    min_size=1
).filter(lambda x: not x.isspace() and '<' not in x and '>' not in x)

# Strategy for generating code content - same as text content
code_content = text_content

# Strategy for generating tags - only alphanumeric and hyphens, like real SO tags
tag = st.text(
    alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd')),
    min_size=1,
    max_size=20
).map(lambda x: x.lower())
tags = st.lists(tag, min_size=0, max_size=5)

# Strategy for generating answer HTML
@st.composite
def answer_html(draw):
    # Generate tags
    question_tags = draw(tags)
    tags_html = ''.join(f'<a class="post-tag">{t}</a>' for t in question_tags)
    
    # Generate multiple answers
    num_answers = draw(st.integers(min_value=1, max_value=3))
    answers = []
    
    for _ in range(num_answers):
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
        '''
        
        # For display_full_answer=True, we expect all parts joined with newlines
        expected_full_answer = '\n'.join(expected_answer_parts).strip()
        # For display_full_answer=False, we expect just the first code block if it exists,
        # otherwise the first text block
        expected_short_answer = (expected_answer_parts[0] if has_code else expected_answer_parts[0]).strip()
        
        answers.append({
            'html': answer_html,
            'expected_short': expected_short_answer,
            'expected_full': expected_full_answer,
            'has_code': has_code
        })
    
    # Build the full HTML with all answers
    full_html = f'''
    <div class="answers">
        {"".join(a['html'] for a in answers)}
    </div>
    <div class="tags">
        {tags_html}
    </div>
    '''
    
    # The function should return the first answer that has code, or the first answer if none have code
    first_code_answer = next((a for a in answers if a['has_code']), answers[0])
    
    return (
        first_code_answer['expected_short'],
        first_code_answer['expected_full'], 
        question_tags,
        full_html
    )

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