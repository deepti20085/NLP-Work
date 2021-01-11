# -*- coding: utf-8 -*-
"""NLPAssig3b.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1exefIHtRFp2sDFmc6NSrxY3hWHeO1Ci7
"""

from google.colab import drive
drive.mount("/content/drive")

!pip3 install afinn
!pip3 install emoji
!pip3 install emot
!pip3 install contractions
!pip3 install nltk
!pip3 install vaderSentiment

!pip3 install demoji

import codecs
import string
import os
import re
from nltk.corpus import wordnet
import contractions
import nltk
import demoji
import pandas as pd
from nltk.tokenize import sent_tokenize, word_tokenize
import emot
from collections import OrderedDict, defaultdict, Counter
from nltk.corpus import sentiwordnet as swn
from afinn import Afinn
from nltk.tag import pos_tag
from sklearn.svm import SVR
import pickle
import nltk.util 
from nltk.util import *
import pairwise

slang_df=pd.read_csv("/content/drive/My Drive/assignment3b/slang4.csv") 
slangDict=dict(zip(slang_df.word,slang_df.fullform))

def readFile(file):
    x=codecs.open(file, 'r', encoding = 'utf-8', errors = 'ignore')
    fileText=x.read()
    #print("read the file")
    return fileText

def elongationReplacer(word):
    """ If the word is an elongated word then change to its valid word else do nothing. """
 
    #WordNet lookup. 
    isNotElongated=wordnet.synsets(word)
    if isNotElongated:
        return word
    else:
        w=re.sub(r'([a-zA-Z0-9\_]*)([a-zA-Z0-9\_])\2([a-zA-Z0-9\_]*)', r'\1', word)
        if (w == word):      
            return word
        else:
            return elongationReplacer(w)

def expandContraction(text):
    text=contractions.fix(text)
    return text

def isUserOrUrl(word):
    regex = r"((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    if(re.search('[@][^\s]+',word) or re.search(regex,word)):
        return True
    else:
        return False

def removeWBPunctuations(word):
    if re.search('^[~][0-9]+(%)$',word):
        word=word[1:]
    elif re.search('^[!"#$%&\\\'()*+, -./:;<=>?@[\]^_`{|}~]+\w+[!"#$%&\\\'()*+, -./:;<=>?@[\]^_`{|}~]+$',word):
        word=word.translate(str.maketrans("","",string.punctuation)) 
    elif re.search('^[!"#$%&\\\'()*+, -./:;<=>?@[\]^_`{|}~]+\w+$',word):
         word=word.translate(str.maketrans("","",string.punctuation))  
    elif re.search('\w+[!"#$%&\\\'()*+, -./:;<=>?@[\]^_`{|}~]+$',word):
         
             word=word.translate(str.maketrans("","",string.punctuation))  
    return word

def isHashTag(word):
    if re.search('^[#]\w+',word):
        return True
    else:
        
        return False

def removePunctionsFromEnd(word):
    if re.search('\w+[!"#$%&\'()*+, -./:;<=>?@[\]^_`{|}~]+$',word):
        word=word.translate(str.maketrans("","",string.punctuation))
    return word

def rectifyVerb(word):
    if (re.search('^[A-Za-z]+(in)$',word) or re.search('^[A-Za-z]+[^i](ng)$',word)):
        w=word[:-2]
        text=word_tokenize(w)
        tag=nltk.pos_tag(text)
        for t in tag:
            if re.search('^(VB)[a-zA-Z]*',t[1]):
                w+='ing'
                return w
            else:
                return word
    else:
        return word

def removeEmoji(text):
    text=demoji.replace(text," ")
    return text

def noisyTermConversion(tweet,slangDict):
    words=""
    x=tweet.split() 
    for w in x:
        word=w
        w=w.lower()
        if w in slangDict: 
            words=words+str(slangDict[w])+" "
        else: 
            words=words+word+" " 
    return words

def isEmoticon(word):
    x=emot.emoticons(word)
    
    if isinstance(x, list):
        for v in x:
            val=v['flag']
    else:
        val=x['flag']
    
    if(val):
        return True
    else:
        return False

def isEmoji(word):
    x=emot.emoji(word)
    if isinstance(x, list):
        for v in x:
            val=v['flag']
    else:
        val=x['flag']
    
    if(val==False):
        return False
    else:
        return True

def recitificationSteps(word):
    if(isEmoticon(word)):
        word=word
    else:
        if(isEmoji(word)):
            words=""
            for w in word:
                if(isEmoji(w)):
                        words=words+" "+w+" "
                else:
                        words+=w
                        wordsTemp=words.split()
                        x=""
                        for w in wordsTemp:
                            if(isEmoji(w)):
                                x=x+w+" "
                            else:    
                                w=removeWBPunctuations(w)
                                # Replace Elongated word with a valid word.
                                w=elongationReplacer(w)
                                # Verb present participle
                                w=rectifyVerb(w)
                                x=x+w+" "
                        word=x        
        else:   
            #remove punctuations from the word boundaries.
            word=removeWBPunctuations(word)
            # Replace Elongated word with a valid word.
            word=elongationReplacer(word)
            # Verb present participle
            word=rectifyVerb(word)
    return word

def preprocessing(slangDict,train_file1,features):
    
    train_data1=readFile(train_file1)
    #expanding contractions
    train_data1=expandContraction(train_data1)
    #remove Emoji 
    #train_data1=removeEmoji(train_data1)
    #print(train_data1)
    data1=train_data1.split('\n')
    tweetsData=[] 
    for data in data1: 
        tweetsData.append(data.replace("\\n", " "))
    #print(tweetsData)    
    #for tweetData in tweetsData:
        #tweet=tweetData.split('\t')[1]
    #print(tweetsData)
    tweets=[d.split('\t') for d in tweetsData]
    del tweets[-1]
    tweetList=[]
    id=[]
    emotion=[]
    intensity_score=[]
    f=0
    for t in tweets:
        tweet=t[1]
        tweet=noisyTermConversion(tweet,slangDict)
        tweetList.append(tweet)
        id.append(t[0])
        emotion.append(t[2])
        if(len(t)==4):
          intensity_score.append(t[3])
          f=1
        #print(t[1])
    #features['id']=id
    features['emotion']=emotion
    if(f==1):
      features['intensity_score']=intensity_score
    #print(tweetList)
    cleanTweetList=[]
    for tweet in tweetList:
        cleantweet=""
        words=tweet.split()
        for word in words:
            #print(word)
            #check if word is @user or url with or without protocol.
            check=isUserOrUrl(word)
            if(check== False):
                #check if word is hashtag.
                index=word.find('#')
                if(index == -1 ):
                    recitificationSteps(word)
                else:
                    words=""
                    if(index>0):
                        y=word[:(index-1)]
                        y=recitificationSteps(y)
                        word=words+" "+y
                        word=word[index:]
                    x=re.findall('#\w+',word)
                    #print(x)
                    for i in x:
                        i=removePunctionsFromEnd(i)
                        w=i[1:]
                        #print(w)
                        w=noisyTermConversion(w,slangDict)
                        w=w.replace(" ","")
                        words=words+" "+"#"+w
                    word=words 
                    #print(word)
            else:
                word=""
            #print(word)
            cleantweet=cleantweet+word+" "
            #print(cleantweet)
        #print(word)
        #print(cleantweet)
        cleanTweetList.append(cleantweet)   
    #print(cleanTweetList)
    return cleanTweetList,features

#print(cleanTweetList)

def createDict(file,exp,wordDict):
    Dict=[]
    words=file.split('\n')
    for word in words:
        word=word.replace('\r','')
        if(word!= ''):
            Dict.append(word)
            wordDict[word].append(exp)
    return Dict ,wordDict

#created dictionary from BING lui lexicon
wordDict=defaultdict(list)
posDict = []
negDict = []
file1=readFile('/content/drive/My Drive/assignment3b/opinion-lexicon-English/negative-words.txt')
file2=readFile('/content/drive/My Drive/assignment3b/opinion-lexicon-English/positive-words.txt')
negDict,wordDict=createDict(file1,'negative',wordDict)
posDict,wordDict=createDict(file2,'positive',wordDict)

#adding MPQA subjectivity lexicon to wordDict
file3=readFile('/content/drive/My Drive/assignment3b/subjectivity_clues_hltemnlp05/subjclueslen1-HLTEMNLP05.txt')
lines=(file3.split('\n'))
lines=[line.split() for line in lines]
for i in range(0,len(lines)-1):
    word=lines[i][2].replace('word1=',"")
    exp=lines[i][5].replace('priorpolarity=','')
    if word not in wordDict:
        wordDict[word].append(exp)

# feature 1 : positive and negative word count
#feature1:Polar word count
def polarWordCount(wordDict,tweets,features):
    #print(tweets)
    pList=[]
    nList=[]
    for tweet in tweets:
        #print(tweet)
        pcount=0
        ncount=0
        tweet=tweet.lower()
        tokens=nltk.word_tokenize(tweet)
        #print(tokens)
        for token in tokens:
            if token in wordDict:
                if (wordDict[token][0]=='positive'):
                    pcount+=1
                elif (wordDict[token][0]=='negative'):
                    ncount+=1    
        pList.append(pcount)
        nList.append(ncount)
    features['pcount']=pList
    features['ncount']=nList
    return features

def isAdjective(tag):
    if tag.startswith('J'):
        return True
    else:
        return False

def isAdverb(tag):
    if tag.startswith('R'):
        return True
    else:
        return False

def isNoun(tag):
    if tag.startswith('N'):
        return True
    else:
        return False

def isVerb(tag):
    if tag.startswith('V'):
        return True
    else:
        return False

def NRCDict(file):
    PolarityScoreDict=defaultdict(list)
    file4=readFile(file)
    #print(file4)
    lines=(file4.split('\n'))
    lines=[line.split() for line in lines]
    for i in range(0,len(lines)-1):
        score=lines[i][1]
        if float(score)>0:
            polarity='positive'
        elif float(score) < 0:
            polarity='negative'
        else:
            polarity='neutral'
        PolarityScoreDict[lines[i][0]].append(polarity)
        PolarityScoreDict[lines[i][0]].append(score)
    return PolarityScoreDict

# feature2: aggregate polarity score
def polarityScore(tweets,features):
    pscore=[]
    nscore=[]
    p1score=[]
    n1score=[]
    p3score=[]
    n3score=[]
    Dict=NRCDict('/content/drive/My Drive/assignment3b/Sentiment140-Lexicon-v0.1/unigrams-pmilexicon.txt')
    #using affin
    afinn = Afinn()
    for tweet in tweets:
        score=afinn.score(tweet)
        if score>0:
            p1score.append(score)
            n1score.append(0.0)
        elif score<0:
            p1score.append(0.0)
            n1score.append(score)
        else:
            p1score.append(0.0)
            n1score.append(0.0)
        #using sentiwordnet  
        p_score=0.0
        n_score=0.0
        p3_score=0.0
        n3_score=0.0
        tokens=nltk.word_tokenize(tweet)
        tokens=pos_tag(tokens)
        for token in tokens:
            f=0
            if isNoun(token[1]):
                #print()
                v='n'
                f=1
            elif isAdverb(token[1]):
                v='r'
                f=1
            elif isVerb(token[1]):
                v='v'
                f=1 
            elif isAdjective(token[1]):
                v='a'
                f=1
            if f==1:
              if (v=='n' or v=='r' or v=='v' or v=='a'):
                  s=list(swn.senti_synsets(token[0].lower(),v))
                  if (len(s)>0):
                      s=s[0]
                      p_score+=s.pos_score()
                      n_score+=s.neg_score()
            t=token[0].lower()
            if t in Dict:
                if (Dict[t][0]=='positive'):
                    p3_score+=float(Dict[t][1])
                elif (Dict[t][0]=='negative'):
                    n3_score+=float(Dict[t][1])        
                    
        pscore.append(p_score)
        nscore.append(n_score)
        p3score.append(p3_score)
        n3score.append(n3_score)
    agg_pos_score_list=[pscore[i] + p1score[i] +p3score[i] for i in range(len(pscore))] 
    agg_neg_score_list=[nscore[i] + n1score[i] +n3score[i] for i in range(len(nscore))] 
    features['aggregate_positive_score']= agg_pos_score_list
    features['aggregate_negative_score']= agg_neg_score_list
    return features

#feature 3
def polarityScoreforHashtag(tweets,features):
    Dict=NRCDict('/content/drive/My Drive/assignment3b/unigrams-pmilexicon.txt')
    #print(Dict)
    pscore=[]
    nscore=[]
    for tweet in tweets:
        p_score=0.0
        n_score=0.0
        tokens=tweet.split()
        for token in tokens:
            t=token.lower()
            #print(t)
            if (re.search('^[#]',t)):
                #print(t)
                if t in Dict:
                    if (Dict[t][0]=='positive'):
                        p_score+=float(Dict[t][1])
                    elif (Dict[t][0]=='negative'):
                        n_score+=float(Dict[t][1])           
        pscore.append(p_score)
        nscore.append(n_score)
    features['Hashtag_positive_score']= pscore
    features['Hashtag_negative_score']= nscore
    
    return features

def emotionDict(e):
    Dict=defaultdict(list)
    file4=readFile('/content/drive/My Drive/assignment3b/NRC-Emotion-Lexicon-Wordlevel-v0.92.txt')
    lines=(file4.split('\n'))
    lines=[line.split() for line in lines]
    for i in range(0,len(lines)-1):
        emotion=lines[i][1]
        if(emotion==e):
            val=lines[i][2]
            Dict[lines[i][0]].append(val)
    return Dict

#feature4
def emotionWordCount(tweets,features):
    Dict=emotionDict('joy')
    sentList=[]
    for tweet in tweets:
        joycount=0
        tweet=tweet.lower()
        tokens=nltk.word_tokenize(tweet)
        for token in tokens:
            if token in Dict:
                joycount+=int(Dict[token][0])  
        sentList.append(joycount)

    Dict=emotionDict('anger')
    aList=[]
    for tweet in tweets:
        acount=0
        tweet=tweet.lower()
        tokens=nltk.word_tokenize(tweet)
        for token in tokens:
            if token in Dict:
                acount+=int(Dict[token][0])  
        aList.append(acount)    

    features['joy_word_count']= sentList
    features['anger_word_count']= aList
    return features

#feature 5: emoticon score
def emoticonScore(tweets,features):
    n1score=[]
    p1score=[]
    afinn=Afinn(emoticons=True)
    for tweet in tweets:
        score=afinn.score(tweet)
        if score>0:
                p1score.append(score)
                n1score.append(0.0)
        elif score<0:
                p1score.append(0.0)
                n1score.append(score)
        else:
                p1score.append(0.0)
                n1score.append(0.0)
    features['pos_emoticon_score']=p1score
    features['neg_emoticon_score']=n1score
    return features

#feature6
def aggregateEmotionScoreforHashtag(tweets,features):
    file=readFile('/content/drive/My Drive/assignment3b/NRC-Hashtag-Emotion-Lexicon-v0.2.txt')
    joyDict=defaultdict(list)
    angerDict=defaultdict(list)
    #print(file)
    lines=(file.split('\n'))
    lines=[line.split() for line in lines]
    #print(lines)
    joyList=[]
    angerList=[]
    
    for i in range(0,len(lines)-1):
        if(lines[i][1].startswith('#')):
            emotion=lines[i][0]
            if(emotion=='joy'):
                 joyDict[lines[i][1]].append(lines[i][2])
            if(emotion=='anger'):    
                   angerDict[lines[i][1]].append(lines[i][2])
    
    for tweet in tweets:
        tweet=tweet.lower()
        tokens=tweet.split()
        joy_score=0.0
        anger_score=0.0
        for token in tokens:
            if token in joyDict:
                joy_score+=float(joyDict[token][0])
            elif token in angerDict:
                anger_score+=float(angerDict[token][0])
        joyList.append(joy_score)
        angerList.append(anger_score)    
    features['joy_hashtag_score']=joyList
    features['anger_hashtag_score']=angerList
    return(features)

#feature 7

def vaderSentiment(tweets,features):
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer 
    posList=[]
    negList=[]
    neuList=[]
    compoundList=[]
    s=SentimentIntensityAnalyzer() 
    for tweet in tweets:
        tweet=tweet.lower()  
        tweetDict=s.polarity_scores(tweet) 
        negList.append(tweetDict['neg'])
        neuList.append(tweetDict['neu'])
        posList.append(tweetDict['pos'])
        compoundList.append(tweetDict['compound'])
    features['vader_neg_score']= negList
    features['vader_neu_score']=neuList
    features['vader_pos_score']=posList
    features['vader_compound_score']=compoundList
    return features

!pip3 install vader

#feature8: negation count

def negationCount(tweets,features):
    from textblob import TextBlob
    import pairwise
    from nltk.sentiment.vader import VaderConstants
    neg_count=[]
    for row in tweets:
        # print(row)
        correct_spell=TextBlob(row).correct()
        correct_s=str(correct_spell)
        # print(correct_s)
        word_tokens=nltk.word_tokenize(correct_s)
        # print(word_tokens)
        negct=0
        sid_obj = VaderConstants()
        last_punc=False
        if(len(word_tokens)>0):
          if(word_tokens[len(word_tokens)-1]=='.' or word_tokens[len(word_tokens)-1]==',' or word_tokens[len(word_tokens)-1]==':'or word_tokens[len(word_tokens)-1]==';' or word_tokens[len(word_tokens)-1]=='!' or word_tokens[len(word_tokens)-1]=='?' ):
            last_punc=True
        for word in word_tokens:
             fs=sid_obj.negated([word],include_nt=True)
             if(fs==True and last_punc==True):
               negct = negct+1
        neg_count.append(negct)
        #print(negct)
    #print(neg_count)
    features['negation_count']=neg_count
    return features

#features9: aggregateEmotionScore
def aggregateEmotionScore(tweets,features):
    #df=pd.read_csv('/content/drive/My Drive/assignment3b/NRC-10-expanded.csv',error_bad_lines=False)
    #for data in df.iterrows():
      #print(data[1])
    df = pd.read_csv('/content/drive/My Drive/assignment3b/NRC-10-expanded.csv',sep="\t",header=None)
    #print(df)
    df = df.iloc[1:]
    #print(df)
    finaldf=pd.DataFrame()
    finaldf['word']=df[0]
    finaldf['joy']=df[5]
    finaldf['anger']=df[1]
    #print(finaldf)
    Dict=defaultdict(list)
    for index, row in finaldf.iterrows():
      Dict[row['word']].append(row['joy'])
      Dict[row['word']].append(row['anger'])
    #print(Dict)
    joylist=[]
    angerlist=[]
    for tweet in tweets:
      tweet=tweet.lower()
      tokens=tweet.split()
      jscore=0.0
      ascore=0.0
      for token in tokens:
        if  token in  Dict:
          jscore+=float(Dict[token][0])
          ascore+=float(Dict[token][1])
      joylist.append(jscore) 
      angerlist.append(ascore)
    features['agg_joy_score']=joylist
    features['agg_anger_score']=angerlist
    return features

#feature: ngram feature
def ngram(tweetlist,flag,features):
  import pickle
  tweets=tweetlist[:]
  tweets=[t.lower() for t in tweets]
  from sklearn.feature_extraction.text import CountVectorizer
  from nltk import ngrams
  pkl_file1="/content/drive/My Drive/assignment3b/vectorizer1_unigram.pkl"
  pkl_file2="/content/drive/My Drive/assignment3b/vectorizer2_bigram.pkl"
  if(flag==0):
      vectorizer_1=CountVectorizer(ngram_range=(1,1))
      vectorizer_2=CountVectorizer(ngram_range=(2,2))
      X1=vectorizer_1.fit_transform(tweets)
      unigram=pd.DataFrame(X1.toarray(),columns=vectorizer_1.get_feature_names())
      X2=vectorizer_2.fit_transform(tweets)
      bigram=pd.DataFrame(X2.toarray(),columns=vectorizer_2.get_feature_names())
      
      with open(pkl_file1, 'wb') as file:
          pickle.dump(vectorizer_1, file)
      
      with open(pkl_file2, 'wb') as file:
          pickle.dump(vectorizer_2, file)    
  else:
      with open( pkl_file1, 'rb') as file:
          vectorizer_1= pickle.load(file)
      with open(pkl_file2, 'rb') as file:
          vectorizer_2= pickle.load(file)    
      cv_test1=CountVectorizer(vocabulary=vectorizer_1.get_feature_names())
      X1=cv_test1.fit_transform(tweets)
      unigram=pd.DataFrame(X1.toarray(),columns=vectorizer_1.get_feature_names())
      cv_test2=CountVectorizer(vocabulary=vectorizer_2.get_feature_names())
      X2=cv_test2.fit_transform(tweets)
      bigram=pd.DataFrame(X2.toarray(),columns=vectorizer_2.get_feature_names())
      #X1=vectorizer_1.transform(tweets)
      #unigram=pd.DataFrame(X1.toarray(),columns=vectorizer_1.get_feature_names())
      #X2=vectorizer_2.transform(tweets)
      #bigram=pd.DataFrame(X2.toarray(),columns=vectorizer_2.get_feature_names())
  
  ngram=pd.concat([unigram,bigram], axis=1)  
  print(features)
  print(ngram)
  features=pd.concat([features,ngram],axis=1)
  print(features)
  return features



nltk.download('wordnet')
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
!pip3 install nltk==3.5
!pip3 install vaderSentiment

nltk.download('sentiwordnet')

def lexiconFeatureGeneration(cleanTweetList,features):
  features=vaderSentiment(cleanTweetList,features) 
  features=polarWordCount(wordDict,cleanTweetList,features) 
  features=polarityScore(cleanTweetList,features)     
  features=polarityScoreforHashtag(cleanTweetList,features) 
  features=emotionWordCount(cleanTweetList,features)
  features=emoticonScore(cleanTweetList,features)
  features=aggregateEmotionScore(cleanTweetList,features)
  features=aggregateEmotionScoreforHashtag(cleanTweetList,features) 
  print("entered negation count")
  features=negationCount(cleanTweetList,features)
  return features



# feature generation for training data
train_file1='/content/drive/My Drive/assignment3b/train/joy-ratings-0to1.train.txt'
train_file2='/content/drive/My Drive/assignment3b/train/anger-ratings-0to1.train.txt'
features=pd.DataFrame()
cleanTweetList,features=preprocessing(slangDict,train_file1,features)
features=lexiconFeatureGeneration(cleanTweetList,features)
features.to_pickle("/content/drive/My Drive/assignment3b/dummy.pkl")
unpickled_df = pd.read_pickle("/content/drive/My Drive/assignment3b/dummy.pkl")

features1=pd.DataFrame()
cleanTweetList1,features1=preprocessing(slangDict,train_file2,features1)
features1=lexiconFeatureGeneration(cleanTweetList1,features1)
features1.to_pickle("/content/drive/My Drive/assignment3b/dummy1.pkl")

tweetlist=cleanTweetList[:]
for x in cleanTweetList1:
  tweetlist.append(x)
print(len(tweetlist))

features=pd.read_pickle("/content/drive/My Drive/assignment3b/dummy.pkl")
features=features.append(features1, ignore_index = True) 
features.to_pickle("/content/drive/My Drive/assignment3b/traininiglexiconfeatureSet.pkl")

train_features=ngram(tweetlist,0,features)  
train_features.to_pickle("/content/drive/My Drive/assignment3b/trainingFeatureSet.pkl")

#model
def svmRegression(train_feature_df,pkl_file):
  
  x_train=train_feature_df.drop(['intensity_score','emotion'], axis=1)# dataframe containing all the features
  y_train=train_feature_df['intensity_score']
  from sklearn.svm import SVR
  import pickle
  regressor=SVR(kernel='rbf')
  regressor.fit(x_train,y_train)
  with open(pkl_file, 'wb') as file:
          pickle.dump(regressor, file)

#file1='/content/drive/My Drive/assignment3b/svrmodel1.pkl'

#model
def DecisionTreeRegression(train_feature_df,pkl_file):
  from sklearn.tree import DecisionTreeRegressor
  import pickle
  x_train=train_feature_df.drop(['intensity_score','emotion'], axis=1)# dataframe containing all the features
  y_train=train_feature_df['intensity_score']
  regressor = DecisionTreeRegressor(random_state=0)
  regressor.fit(x_train,y_train)
  with open(pkl_file, 'wb') as file:
      pickle.dump(regressor, file)

#model
def MLPRegression(train_feature_df,pkl_file):
  from sklearn.neural_network import MLPRegressor
  import pickle
  x_train=train_feature_df.drop(['intensity_score','emotion'], axis=1)# dataframe containing all the features
  y_train=train_feature_df['intensity_score']
  regressor=MLPRegressor()
  regressor.fit(x_train,y_train)
  with open(pkl_file, 'wb') as file:
      pickle.dump(regressor, file)

!pip3 install pairwise

#feature generation for test file

features2=pd.DataFrame()
features3=pd.DataFrame()
cleanTweetList3,features2=preprocessing(slangDict,'/content/drive/My Drive/assignment3b/test/joy-ratings-0to1.test.target.txt',features2)
features2=lexiconFeatureGeneration(cleanTweetList3,features2)
cleanTweetList4,features3=preprocessing(slangDict,'/content/drive/My Drive/assignment3b/test/anger-ratings-0to1.test.target.txt',features3)

print(features2)

features3=lexiconFeatureGeneration(cleanTweetList4,features3)

#features2=features2.append(features3, ignore_index= True) 
#for x in cleanTweetList4:
 #cleanTweetList3.append(x)

features4=pd.DataFrame()
features4=features2

test_features_joy=ngram(cleanTweetList3,1,features2)

features5=pd.DataFrame()
features5=features3
test_features_anger=ngram(cleanTweetList4,1,features3)

#fitting the  svm regressor model
trainingset_features=pd.read_pickle("/content/drive/My Drive/assignment3b/trainingFeatureSet.pkl")
print(trainingset_features)
pkl_file='/content/drive/My Drive/assignment3b/svrmodel1_1.pkl'
svmRegression(trainingset_features,pkl_file)

#fitting the  decision tree regression model
pkl_file='/content/drive/My Drive/assignment3b/DecisionTreemodel1.pkl'
DecisionTreeRegression(trainingset_features,pkl_file)

#fitting  svm regressor on lexicon features
train_lexfeature=pd.read_pickle('/content/drive/My Drive/assignment3b/traininiglexiconfeatureSet.pkl')
pkl_file='/content/drive/My Drive/assignment3b/svrmodel1_2.pkl'
svmRegression(train_lexfeature,pkl_file)

#fitting mlp regressor
trainingset_features=pd.read_pickle("/content/drive/My Drive/assignment3b/trainingFeatureSet.pkl")
pkl_file='/content/drive/My Drive/assignment3b/MLPmodel1.pkl'
MLPRegression(trainingset_features,pkl_file)

#prediction for joy and anger file for svr
import pickle
with open('/content/drive/My Drive/assignment3b/svrmodel1.pkl', 'rb') as file:
    svr1_pickle_model = pickle.load(file)
x_test_anger=test_features_anger.drop(['intensity_score','emotion'], axis=1)# dataframe containing all the features
x_test_joy=test_features_joy.drop(['intensity_score','emotion'], axis=1)
y_predict_anger=svr1_pickle_model.predict(x_test_anger)
y_predict_joy=svr1_pickle_model.predict(x_test_joy)



#prediction for joy and anger for decision tree classifier
import pickle
with open('/content/drive/My Drive/assignment3b/DecisionTreemodel1.pkl', 'rb') as file:
    dt_pickle_model = pickle.load(file)
x_test_anger=test_features_anger.drop(['intensity_score','emotion'], axis=1)# dataframe containing all the features
x_test_joy=test_features_joy.drop(['intensity_score','emotion'], axis=1)
y_predict_anger=dt_pickle_model.predict(x_test_anger)
y_predict_joy=dt_pickle_model.predict(x_test_joy)

#prediction for joy and anger for decision tree classifier
import pickle
with open('/content/drive/My Drive/assignment3b/MLPmodel1.pkl', 'rb') as file:
    mlp_pickle_model = pickle.load(file)
x_test_anger=test_features_anger.drop(['intensity_score','emotion'], axis=1)# dataframe containing all the features
x_test_joy=test_features_joy.drop(['intensity_score','emotion'], axis=1)
y_predict_anger_mlp=mlp_pickle_model.predict(x_test_anger)
y_predict_joy_mlp=mlp_pickle_model.predict(x_test_joy)

print(len(y_predict_anger),len(y_predict_joy))

#generating predicted test file.
def predictedTestFile(file):
  df=pd.DataFrame(columns=['id','tweet','emotion','intensity'])
  file=readFile(file)
  data=file.split('\n')
  data=data[:-1]
  for line in data:
      words=line.split('\t')
      df = df.append({'id' :words[0] ,'tweet':words[1],'emotion':words[2] , 'intensity' :words[3]} , ignore_index=True)
  return df

joy_df=predictedTestFile('/content/drive/My Drive/assignment3b/test/joy-ratings-0to1.test.target.txt')
anger_df=predictedTestFile('/content/drive/My Drive/assignment3b/test/anger-ratings-0to1.test.target.txt')

y_predict_joy=list(y_predict_joy)
y_predict_anger=list(y_predict_anger)
joy_df['intensity']=y_predict_joy
anger_df['intensity']=y_predict_anger

y_predict_joy_mlp=list(y_predict_joy_mlp)
y_predict_anger_mlp=list(y_predict_anger_mlp)
joy_df['intensity']=y_predict_joy_mlp
anger_df['intensity']=y_predict_anger_mlp

import numpy
numpy.savetxt('/content/drive/My Drive/assignment3b/svrmodel1JOYprediction.txt', joy_df.values, fmt='%s', delimiter="\t")

import numpy
numpy.savetxt('/content/drive/My Drive/assignment3b/svrmodel1ANGERprediction.txt',anger_df.values, fmt='%s', delimiter="\t")

import numpy
numpy.savetxt('/content/drive/My Drive/assignment3b/dt1_JOYprediction.txt', joy_df.values, fmt='%s', delimiter="\t") 
numpy.savetxt('/content/drive/My Drive/assignment3b/dt1_ANGERprediction.txt',anger_df.values, fmt='%s', delimiter="\t")

dt_df_combine=pd.DataFrame()
dt_df_combine=anger_df.append(joy_df, ignore_index=True)

numpy.savetxt('/content/drive/My Drive/assignment3b/dt1_COMBINEprediction.txt',dt_df_combine.values, fmt='%s', delimiter="\t")

import numpy
numpy.savetxt('/content/drive/My Drive/assignment3b/mlp1_JOYprediction.txt', joy_df.values, fmt='%s', delimiter="\t") 
numpy.savetxt('/content/drive/My Drive/assignment3b/mlp1_ANGERprediction.txt',anger_df.values, fmt='%s', delimiter="\t")

