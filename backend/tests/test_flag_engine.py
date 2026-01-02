"""
Tests for the Flag Engine.
"""

import pytest
from uuid import uuid4

from app.core.crypto import CryptoService


class TestCryptoService:
    """Test suite for the CryptoService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.crypto = CryptoService(secret_key="test-secret-key-for-testing")
    
    def test_hash_semantic_truth(self):
        """Test that semantic truth is hashed consistently."""
        truth = "admin_password_reuse"
        hash1 = self.crypto.hash_semantic_truth(truth)
        hash2 = self.crypto.hash_semantic_truth(truth)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex
    
    def test_hash_semantic_truth_normalization(self):
        """Test that semantic truth normalization works."""
        hash1 = self.crypto.hash_semantic_truth("Admin_Password")
        hash2 = self.crypto.hash_semantic_truth("  admin_password  ")
        
        assert hash1 == hash2
    
    def test_generate_flag(self):
        """Test flag generation."""
        user_id = str(uuid4())
        case_id = str(uuid4())
        truth_hash = self.crypto.hash_semantic_truth("test_answer")
        
        flag = self.crypto.generate_flag(user_id, case_id, truth_hash)
        
        assert flag.startswith("FORENSIC{")
        assert flag.endswith("}")
        assert len(flag) > 20
    
    def test_flag_uniqueness_per_user(self):
        """Test that different users get different flags."""
        user1_id = str(uuid4())
        user2_id = str(uuid4())
        case_id = str(uuid4())
        truth_hash = self.crypto.hash_semantic_truth("test_answer")
        
        flag1 = self.crypto.generate_flag(user1_id, case_id, truth_hash)
        flag2 = self.crypto.generate_flag(user2_id, case_id, truth_hash)
        
        assert flag1 != flag2
    
    def test_flag_uniqueness_per_case(self):
        """Test that same user gets different flags for different cases."""
        user_id = str(uuid4())
        case1_id = str(uuid4())
        case2_id = str(uuid4())
        truth_hash = self.crypto.hash_semantic_truth("test_answer")
        
        flag1 = self.crypto.generate_flag(user_id, case1_id, truth_hash)
        flag2 = self.crypto.generate_flag(user_id, case2_id, truth_hash)
        
        assert flag1 != flag2
    
    def test_verify_flag_correct(self):
        """Test that correct flags verify successfully."""
        user_id = str(uuid4())
        case_id = str(uuid4())
        truth_hash = self.crypto.hash_semantic_truth("test_answer")
        
        flag = self.crypto.generate_flag(user_id, case_id, truth_hash)
        is_valid = self.crypto.verify_flag(flag, user_id, case_id, truth_hash)
        
        assert is_valid is True
    
    def test_verify_flag_wrong_user(self):
        """Test that flags don't verify for wrong user."""
        user1_id = str(uuid4())
        user2_id = str(uuid4())
        case_id = str(uuid4())
        truth_hash = self.crypto.hash_semantic_truth("test_answer")
        
        flag = self.crypto.generate_flag(user1_id, case_id, truth_hash)
        is_valid = self.crypto.verify_flag(flag, user2_id, case_id, truth_hash)
        
        assert is_valid is False
    
    def test_verify_flag_tampered(self):
        """Test that tampered flags don't verify."""
        user_id = str(uuid4())
        case_id = str(uuid4())
        truth_hash = self.crypto.hash_semantic_truth("test_answer")
        
        flag = self.crypto.generate_flag(user_id, case_id, truth_hash)
        tampered_flag = flag[:-5] + "XXXXX"
        is_valid = self.crypto.verify_flag(tampered_flag, user_id, case_id, truth_hash)
        
        assert is_valid is False
    
    def test_verify_answer_correct(self):
        """Test that correct answers verify successfully."""
        answer = "admin_password_reuse"
        truth_hash = self.crypto.hash_semantic_truth(answer)
        
        is_correct = self.crypto.verify_answer(answer, truth_hash)
        
        assert is_correct is True
    
    def test_verify_answer_normalized(self):
        """Test that answers are normalized before verification."""
        answer = "  Admin_Password_Reuse  "
        truth_hash = self.crypto.hash_semantic_truth("admin_password_reuse")
        
        is_correct = self.crypto.verify_answer(answer, truth_hash)
        
        assert is_correct is True
    
    def test_verify_answer_wrong(self):
        """Test that wrong answers don't verify."""
        truth_hash = self.crypto.hash_semantic_truth("admin_password_reuse")
        
        is_correct = self.crypto.verify_answer("wrong_answer", truth_hash)
        
        assert is_correct is False
