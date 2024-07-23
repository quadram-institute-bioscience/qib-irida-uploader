import unittest
from unittest.mock import patch, MagicMock
import tempfile
import os
import configparser
from click.testing import CliRunner
import atexit

# Import the functions and classes you want to test
from irida import (
    get_config_value,
    initialize_irida_api,
    create_project,
    prepare,
    upload,
)


class TestIRIDAUploaderFunctions(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_get_config_value(self):
        config = configparser.ConfigParser()
        config["Settings"] = {"test_key": "test_value"}

        # Test getting value from config
        self.assertEqual(
            get_config_value(config, "Settings", "test_key", "TEST_ENV", "Test prompt"),
            "test_value",
        )

        # Test getting value from environment
        with patch.dict("os.environ", {"TEST_ENV": "env_value"}):
            self.assertEqual(
                get_config_value(
                    config, "Settings", "non_existent", "TEST_ENV", "Test prompt"
                ),
                "env_value",
            )

        # Test getting value from prompt (mocking click.prompt)
        with patch("click.prompt", return_value="prompt_value"):
            self.assertEqual(
                get_config_value(
                    config,
                    "Settings",
                    "non_existent",
                    "NON_EXISTENT_ENV",
                    "Test prompt",
                ),
                "prompt_value",
            )

    @patch('iridauploader.core.api_handler._initialize_api')
    @patch('click.prompt')
    def test_initialize_irida_api(self, mock_prompt, mock_initialize_api):
        mock_api = MagicMock()
        mock_initialize_api.return_value = mock_api

        # Set up mock prompts
        mock_prompt.side_effect = [
            "http://test.com",  # base_url
            "test_client_id",  # client_id
            "test_client_secret",  # client_secret
            "test_username",  # username
            "test_password",  # password
            "30",  # timeout
        ]

        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.conf') as temp_config:
            temp_config.write('[Settings]\nbase_url=http://test.com\n')
            temp_config.flush()
            
            # Keep track of registered atexit functions
            original_atexit_register = atexit.register
            registered_funcs = []
            
            def mock_atexit_register(func, *args, **kwargs):
                registered_funcs.append((func, args, kwargs))
                return original_atexit_register(func, *args, **kwargs)
            
            with patch('atexit.register', side_effect=mock_atexit_register):
                api, config_path = initialize_irida_api(temp_config.name)
            
            self.assertEqual(api, mock_api)
            self.assertTrue(os.path.exists(config_path))
            
            # Verify that prompts were called
            self.assertEqual(mock_prompt.call_count, 5)

            # Manually remove the atexit callback
            for func, args, kwargs in registered_funcs:
                if func == os.unlink and args and args[0] == config_path:
                    atexit.unregister(func)
                    break
            
            # Clean up
            try:
                os.unlink(config_path)
            except FileNotFoundError:
                pass  # File might have been already deleted

        # Clean up the original temp file
        try:
            os.unlink(temp_config.name)
        except FileNotFoundError:
            pass  # File might have been already deleted

    @patch("iridauploader.core.api_handler._initialize_api")
    @patch('click.prompt')
    def test_create_project(self, mock_prompt, mock_initialize_api):
        mock_api = MagicMock()
        mock_api.get_projects.return_value = []
        mock_api.send_project.return_value = {"resource": {"identifier": "123"}}
        mock_initialize_api.return_value = mock_api

        # Set up mock prompts
        mock_prompt.side_effect = [
            "http://test.com",  # base_url
            "test_client_id",  # client_id
            "test_client_secret",  # client_secret
            "test_username",  # username
            "test_password",  # password
            "30",  # timeout
        ]

        project_id = create_project("Test Project", "test_config.conf")

        self.assertEqual(project_id, "123")
        mock_api.send_project.assert_called_once()

    @patch("irida.create_project")
    def test_prepare(self, mock_create_project):
        mock_create_project.return_value = "123"

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create dummy fastq files
            open(os.path.join(temp_dir, "sample1_R1_001.fastq.gz"), "w").close()
            open(os.path.join(temp_dir, "sample1_R2_001.fastq.gz"), "w").close()

            result = self.runner.invoke(prepare, [temp_dir, "--pe"])

            self.assertEqual(result.exit_code, 0)
            self.assertTrue(os.path.exists(os.path.join(temp_dir, "SampleList.csv")))

    @patch("irida._upload")
    @patch("irida.initialize_irida_api")
    @patch("irida._config.set_config_file")
    @patch("irida._config.setup")
    def test_upload(self, mock_config_setup, mock_set_config_file, mock_initialize_api, mock_upload):
        mock_api = MagicMock()
        mock_upload.return_value = 0

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a temporary config file
            temp_config_path = os.path.join(temp_dir, "temp_config.conf")
            config = configparser.ConfigParser()
            config['Settings'] = {
                'base_url': 'http://test.com',
                'client_id': 'test_client',
                'client_secret': 'test_secret',
                'username': 'test_user',
                'password': 'test_pass',
                'timeout': '30'
            }
            with open(temp_config_path, 'w') as configfile:
                config.write(configfile)

            mock_initialize_api.return_value = (mock_api, temp_config_path)

            # Create dummy SampleList.csv
            with open(os.path.join(temp_dir, "SampleList.csv"), "w") as f:
                f.write("Sample_Name,Project_ID,File_Forward,File_Reverse\n")
                f.write("sample1,123,sample1_R1.fastq.gz,sample1_R2.fastq.gz\n")

            result = self.runner.invoke(upload, [temp_dir, '--config', temp_config_path])

            self.assertEqual(result.exit_code, 0)
            mock_upload.assert_called_once()
            mock_set_config_file.assert_called_once_with(temp_config_path)
            mock_config_setup.assert_called_once()

if __name__ == "__main__":
    unittest.main()
