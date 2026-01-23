import re

def clean_text(text):
    # Split text into sentences using Chinese punctuation
    sentences = re.split(r'([。！？])', text)
    
    cleaned_sentences = []
    for i in range(0, len(sentences) - 1, 2):
        sentence = sentences[i] + sentences[i + 1]
        # Filter: length > 5, not starting with non-Chinese, etc.
        if len(sentence.strip()) > 5 and not sentence.strip().startswith(('http', '#', '[')):
            cleaned_sentences.append(sentence.strip())
    
    return '\n'.join(cleaned_sentences)

if __name__ == "__main__":
    # Example usage
    sample_text = """
    在股票市场中，新概念三是一种重要的技术分析工具，它被广泛应用于选股和预测股价走势。新概念三属于中级的技术水平，在技术指标中具有较高的可靠性和准确性。新概念三是由均线系统、动能指标和成交量指标组合而成的，可以辅助投资者判断股票走势和选取适合的买入或卖出时机。它主要通过分析股票的价格趋势、成交量、动量等方面的变化来判断市场的供求关系和买卖力量的强弱，从而提供有效的投资决策依据。在股票技术分析中，新概念三可用于识别并确认股票的主要趋势，包括上升趋势、下降趋势和横盘整理趋势。通过观察均线系统的金叉和死叉现象，投资者可以判断股票的买入和卖出信号；动能指标的运行可以帮助投资者衡量市场的买卖力量；成交量指标则可以反映市场的活跃程度和资金的流入流出情况。总之，新概念三在股票投资技术分析中扮演着重要的角色。它可以帮助投资者把握市场的主要走势，并提供有效的买卖信号。然而，投资者在使用新概念三进行技术分析时，还应结合其他指标和研究方法，以形成更完整和准确的判断。
    #新概念三#
    [相关标签]
    """
    cleaned = clean_text(sample_text)
    print(cleaned)