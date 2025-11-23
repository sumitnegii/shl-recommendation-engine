import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class SHLRecommender:
    def __init__(self, csv_path: str = "assessments.csv"):
        try:
            self.df = pd.read_csv(csv_path)
            logger.info(f"Loaded dataset with {len(self.df)} assessments")
            
            # Data validation
            required_columns = ['name', 'description', 'skills_required', 'domain', 'level']
            missing_columns = [col for col in required_columns if col not in self.df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Preprocess text data 
            self.df = self.df.fillna('')
            self.df["combined_text"] = self._create_combined_text()
            
            
            self.vectorizer = TfidfVectorizer(
                stop_words="english",
                ngram_range=(1, 3),
                min_df=2,
                max_df=0.8,
                sublinear_tf=True  
            )
            
            self.catalogue_tfidf = self.vectorizer.fit_transform(self.df["combined_text"].values)
            logger.info("TF-IDF vectorizer trained successfully")
            
        except Exception as e:
            logger.error(f"Error initializing recommender: {e}")
            raise

    def _create_combined_text(self) -> pd.Series:
        """Create combined text with weighted fields"""
        texts = []
        for _, row in self.df.iterrows():
            # Weight different fields differently
            parts = [
                row['name'] * 3,  # Highest weight for name
                row['description'] * 2,  # Medium weight for description
                row['skills_required'],  # Standard weight for skills
                row['domain'] * 2,  # Medium weight for domain
                row['level']  # Standard weight for level
            ]
            texts.append(' '.join(parts))
        return pd.Series(texts)

    def _preprocess_user_input(self, user_input: Dict[str, Any]) -> str:
        """Preprocess and weight user input"""
        parts = []
        
        # Job role - highest weight
        if user_input.get("job_role"):
            parts.extend([user_input['job_role']] * 3)
        
        # Skills - high weight
        if user_input.get("skills"):
            skills_text = user_input['skills'].replace(',', ' ')
            parts.extend([skills_text] * 2)
        
        # Experience - contextual weighting
        if user_input.get("experience") is not None:
            exp = user_input['experience']
            if exp < 2:
                level_keywords = ["beginner", "fundamental", "introduction"]
            elif exp < 5:
                level_keywords = ["intermediate", "practical", "essential"]
            else:
                level_keywords = ["advanced", "expert", "master", "strategic"]
            parts.extend(level_keywords)
        
        # Goal - medium weight......
        if user_input.get("goal"):
            parts.append(user_input['goal'])
        
        return ' '.join(parts)

    def _calculate_skill_match(self, user_skills: set, assessment_skills: str) -> float:
        """Calculate skill matching score with partial matching"""
        assessment_skills_set = set(s.strip().lower() for s in str(assessment_skills).split(";") if s.strip())
        
        if not assessment_skills_set:
            return 0.0
        
        # Exact matches
        exact_matches = len(user_skills & assessment_skills_set)
        
        # Partial matches (substring matches)
        partial_matches = 0
        for user_skill in user_skills:
            for assessment_skill in assessment_skills_set:
                if user_skill in assessment_skill or assessment_skill in user_skill:
                    partial_matches += 0.5  # Lower weight for partial matches
                    break # can improve using KMP Algo 
        
        total_matches = exact_matches + partial_matches
        return min(total_matches / len(assessment_skills_set), 1.0)

    def recommend(self, user_input: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
        try:
            # Preprocess  skills
            user_skills = set(
                s.strip().lower() 
                for s in user_input.get("skills", "").split(",") 
                if s.strip()
            )
            
            # Prepare  text for TF-IDF
            user_text = self._preprocess_user_input(user_input)
            if not user_text.strip():
                logger.warning("Empty user input after preprocessing")
                return []
            
            # Calculate text similarity
            q_vec = self.vectorizer.transform([user_text])
            text_similarities = cosine_similarity(q_vec, self.catalogue_tfidf)[0]
            
            # Calculate skill matches
            skill_matches = []
            for skills_str in self.df["skills_required"]:
                match_score = self._calculate_skill_match(user_skills, skills_str)
                skill_matches.append(match_score)
            
            # Combine scores (adjust weights as needed)
            skill_match_array = np.array(skill_matches)
            combined_scores = 0.7 * text_similarities + 0.3 * skill_match_array
            
            # Get top recommendations
            top_indices = np.argsort(combined_scores)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                if combined_scores[idx] > 0.01:  # Minimum similarity threshold
                    results.append({
                        "name": self.df.iloc[idx]["name"],
                        "description": self.df.iloc[idx]["description"],
                        "domain": self.df.iloc[idx]["domain"],
                        "level": self.df.iloc[idx]["level"],
                        "score": float(combined_scores[idx])
                    })
            
            logger.info(f"Generated {len(results)} recommendations with scores ranging from "
                       f"{min([r['score'] for r in results]) if results else 0:.3f} to "
                       f"{max([r['score'] for r in results]) if results else 0:.3f}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in recommendation process: {e}")
            return []

    def get_assessment_count(self) -> int:
        """Get total number of assessments in catalogue"""
        return len(self.df)