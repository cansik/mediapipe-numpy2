import unittest

import mediapipe as mp
import numpy as np


class TestPoseEstimator(unittest.TestCase):
    def test_pose_estimator_on_zero_image(self):
        # create a blank RGB image
        image = np.zeros((480, 640, 3), dtype=np.uint8)

        mp_pose = mp.solutions.pose
        with mp_pose.Pose(static_image_mode=True) as pose:
            results = pose.process(image)

        # We got a results object
        self.assertIsNotNone(results)

        # It should have a pose_landmarks attribute
        self.assertTrue(hasattr(results, "pose_landmarks"))

        # If landmarks were detected, they should be a numpy array
        if results.pose_landmarks is not None:
            self.assertIsInstance(results.pose_landmarks, np.ndarray)
            # 33 keypoints × (x, y, z)
            self.assertEqual(results.pose_landmarks.ndim, 2)
            self.assertEqual(results.pose_landmarks.shape[1], 3)


if __name__ == "__main__":
    unittest.main()
