import chalk from 'chalk';

export class Logger {
  static info(message: string): void {
    console.log(chalk.blue('ℹ'), message);
  }

  static success(message: string): void {
    console.log(chalk.green('✓'), message);
  }

  static error(message: string): void {
    console.log(chalk.red('✗'), message);
  }

  static warn(message: string): void {
    console.log(chalk.yellow('⚠'), message);
  }

  static step(message: string): void {
    console.log(chalk.cyan('→'), message);
  }

  static heading(message: string): void {
    console.log('\n' + chalk.bold.underline(message) + '\n');
  }
}
